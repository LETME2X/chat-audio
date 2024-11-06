from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import base64
import os
import time
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from .supabase import supabase 

# Logging setup 
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Environment variables loading
load_dotenv()

# Gemini API key setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

def process_audio_data(audio_base64: str) -> bytes:
    """Convert base64 audio data to bytes."""
    try:
        if 'base64,' in audio_base64:
            audio_base64 = audio_base64.split('base64,')[1]
        return base64.b64decode(audio_base64)
    except Exception as e:
        logger.error(f"Error processing audio data: {str(e)}")
        raise

@app.on_event("startup")
async def startup():
    try:
        await supabase.postgrest.schema_cache.refresh()
        print("Schema cache refreshed successfully")
    except Exception as e:
        print(f"Error refreshing schema cache: {e}")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database enum ke hisaab se status values
STATUS = {
    'INITIAL': 'received',
    'PENDING': 'processing',
    'SUCCESS': 'completed',
    'ERROR': 'error'
}

async def store_message(data: dict):
    """Helper function to store messages in Supabase"""
    try:
        status = data.get('status', 'received')
        if status not in STATUS.values():
            status = 'received'
            
        message_data = {
            'message': data.get('message', ''),
            'is_ai': data.get('is_ai', False),
            'session_type': data.get('session_type', 'temporary'),
            'status': status,
            'temp_user_id': data.get('temp_user_id'),
            'user_id': data.get('user_id'),
            'audio_url': data.get('audio_url'),
            'transcription': data.get('transcription'),
            'analysis': data.get('analysis'),
            'reply': data.get('reply')
        }
        
        if 'audio_url' in data:
            message_data['audio_url'] = data['audio_url']
        if 'processing_time' in data:
            message_data['processing_time'] = data['processing_time']
        if 'transcription' in data:
            message_data['transcription'] = data['transcription']
            
        response = supabase.table('messages').insert(message_data).execute()
        return response.data
    except Exception as e:
        print(f"✗ Database error: {str(e)}")
        return {"error": str(e)}

async def process_audio_with_gemini(audio_bytes):
    """Process audio with Gemini Flash model"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        logger.debug("Processing audio with Gemini...")
        
        prompt = [
            {
                "text": """
             You are a highly perceptive listener who captures every word exactly as spoken while also noting the natural flow and feeling in speech. Your goal is to create perfect, easy-to-read transcriptions.

            **1. TRANSCRIPTION PRIORITIES:**

            PRIMARY FOCUS:
               - Capture every single word exactly
               - Note natural speech patterns
               - Add simple feeling markers
               - Keep everything readable
               - Listen multiple times for accuracy

            WHAT TO CAPTURE:
               1. Exact Words:
                  - Every word as spoken
                  - Cut-off words
                  - Fillers (um, uh, like)
                  - Repeated words
                  - Pauses
                  - Trailing off

               2. Speech Patterns:
                  - Stutters exactly (I-I-I)
                  - Restarts (I want- I need)
                  - Common words (gonna, wanna)
                  - [talks faster/slower]
                  - [speaks softer/louder]

               3. Simple Feelings:
                  - [happy] or [excited]
                  - [nervous] or [unsure]
                  - [sad] or [upset]
                  - [sure] or [strong]
                  - [tired] or [lively]

               4. Natural Moments:
                  - [laughs]
                  - [sighs]
                  - [breathes]
                  - [pauses]
                  - [clears throat]

            HOW TO WRITE IT:
               1. Keep It Simple:
                  - Use [] for actions and feelings
                  - Use ... for trailing off
                  - Write stutters as heard (I-I-I)
                  - Use everyday words
                  - Keep it natural

               2. Stay Clear:
                  - Write exactly what you hear
                  - Use simple words
                  - Make it easy to read
                  - Show natural speech flow
                  - Keep feeling markers simple

               3. Main Points:
                  - Exact words come first
                  - Simple feeling notes
                  - Basic action notes
                  - Clear speech patterns
                  - Easy to read

            VERIFICATION STEPS:
               □ Got every word exactly?
               □ Are feeling markers simple?
               □ Does it read naturally?
               □ Noted speech patterns?
               □ Listened multiple times?

            YOUR COMMITMENT:
            "I capture every word perfectly and note feelings simply. I make transcriptions anyone can read easily. 
            I use simple [] markers, write stutters exactly, and use everyday words. I will listen multiple times 
            to get everything right."

            EXAMPLE OF GOOD TRANSCRIPTION:
            [nervous] I-I need to... [pause] tell you something [speaks softer] really important [breathes] 
            [more confident] I've been thinking about this.

            Remember: Write it like you're describing a conversation to a friend. Get every word exactly right, 
            and use simple [] markers for feelings and actions. If you can't say it simply, try a different way.


                **2. Communication Analysis:**
                As a communication coach, provide one specific piece of actionable advice or positive feedback based on the *transcription*. Focus on a single aspect that the speaker could improve or that they did particularly well. Keep it brief, friendly, and conversational. Begin with "Communication Tip:".

                **3. Conversational Response:**
                Respond ONLY to what you heard in the audio recording. Keep your response natural and conversational, but stick strictly to what the person actually said in their audio message. Don't make assumptions or add information that wasn't in the recording. Be friendly and engaging while ensuring your response directly relates to the specific content of their audio message.

                **Output Format:**
                ```
                ---TRANSCRIPTION---
                [Your detailed transcription here]

                ---ANALYSIS---
                Communication Tip: [Your communication tip here]

                ---RESPONSE---
                [Your conversational response here]
                ```
                """
            },
            {
                "inline_data": {
                    "mime_type": "audio/wav",
                    "data": base64.b64encode(audio_bytes).decode('utf-8')
                }
            }
        ]

        response = model.generate_content(prompt)#calling api one time only
        
        if response and hasattr(response, 'text') and response.text:
            text = response.text.strip().replace('```', '').strip()
            # Teeno sections ke liye result dictionary
            result = {
                'transcription': '',
                'analysis': '',
                'reply': ''
            }
            
            # Split by section markers and process each section
            if '---TRANSCRIPTION---' in text:
                transcription_part = text.split('---TRANSCRIPTION---')[1].split('---ANALYSIS---')[0].strip()
                result['transcription'] = transcription_part
                
            if '---ANALYSIS---' in text:
                analysis_part = text.split('---ANALYSIS---')[1].split('---RESPONSE---')[0].strip()
                result['analysis'] = analysis_part
                
            if '---RESPONSE---' in text:
                response_part = text.split('---RESPONSE---')[1].strip()
                result['reply'] = response_part.replace('```', '').strip()
            
            # content there or not
            if not any(value.strip() for value in result.values()):
                logger.error("No content found in parsed sections")
                return None
                
            return result
        
        logger.error("No valid response from Gemini")
        return None

    except Exception as e:
        logger.error(f"Error processing with Gemini: {str(e)}")
        return None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data['type'] == 'audio':
                try:
                    start_time = time.time()
                    audio_bytes = process_audio_data(data['audio'])
                    
                    # Send processing status
                    await websocket.send_json({
                        'type': 'status',
                        'message': 'Processing audio...'
                    })
                    
                    result = await process_audio_with_gemini(audio_bytes)
                    
                    if result and result.get('transcription'):
                        # Send transcription and analysis together
                        await websocket.send_json({
                            'type': 'transcription',
                            'text': result['transcription'],
                            'analysis': result['analysis']
                        })
                        
                        # Storing user message
                        await store_message({
                            'user_id': data.get('userId'),
                            'temp_user_id': data.get('tempUserId'),
                            'message': result['transcription'],
                            'is_ai': False,
                            'session_type': 'logged-in' if data.get('userId') else 'temporary',
                            'status': STATUS['SUCCESS'],
                            'transcription': result['transcription'],
                            'analysis': result['analysis'],
                            'audio_url': data.get('audio_url'),
                            'audio_duration': data.get('duration'),
                            'audio_format': 'wav',
                            'processing_time': time.time() - start_time
                        })
                        
                        # AI reply separately
                        if result.get('reply'):
                            await websocket.send_json({
                                'type': 'ai_reply',
                                'text': result['reply']
                            })
                            
                            await store_message({
                                'user_id': data.get('userId'),
                                'temp_user_id': data.get('tempUserId'),
                                'message': result['reply'],
                                'is_ai': True,
                                'session_type': 'logged-in' if data.get('userId') else 'temporary',
                                'status': STATUS['SUCCESS'],
                                'reply': result['reply']
                            })
                    else:
                        await websocket.send_json({
                            'type': 'error',
                            'message': 'Failed to process audio'
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    await websocket.send_json({
                        'type': 'error',
                        'message': str(e)
                    })
                    
    except WebSocketDisconnect:
        pass

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.strftime('%H:%M:%S')}

if __name__ == "__main__":
    import uvicorn
    print(f"\n→ Starting server at {time.strftime('%H:%M:%S')}")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)