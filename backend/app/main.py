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
import aiohttp
import asyncio
from async_timeout import timeout  

#Logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Loading environment variables
load_dotenv()

# Gemini API key
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

# Status values matching database enum
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
                You are a highly perceptive AI assistant designed to understand and analyze spoken communication with exceptional detail, including variations in English accents such as Indian English, British English, and American English.  You will receive an audio recording. Your task is to process this audio and provide three distinct outputs: a rich transcription, a communication analysis, and a conversational response.

                **1. Rich Transcription:**
                Transcribe the audio, paying close attention to the speaker's accent and pronunciation. Regardless of the specific English accent (Indian, British, American, or other), aim to accurately capture the spoken words and reconstruct the intended meaning, even if the speech is fragmented or incomplete. Create a smooth, flowing, and grammatically correct transcription.  Do not try to "correct" the speaker's pronunciation or word choices to match a specific accent; instead, transcribe what you hear faithfully.

                Use the following markup to capture the full spectrum of vocal expression (adapt the markup to the specific accent if necessary):

                * **Emotions:**  Use precise emotion labels (e.g., [joyful], [frustrated], [anxious], [sarcastic], [contemplative]). Include intensity modifiers ([slightly], [very], [extremely]). For mixed emotions: [emotion1-emotion2].  If unsure: [uncertain emotion: description of vocal cues].
                * **Speech Pattern Classification:**
                  
                  IMPORTANT: DO NOT classify normal speech patterns as stutters!
                  
                  1. Regular Speech Patterns (DO NOT mark as stutters):
                     - Natural pauses between words
                     - Thinking pauses
                     - Word emphasis
                     - Slow or fast speech
                     - Voice trailing off
                     - Normal hesitations
                     - End of sentence pauses
                  
                  2. True Stuttering (ONLY mark if clearly present):
                     - Must have clear, unambiguous sound/word repetition
                     - Example: "I-I-I want" (actual repetition)
                     - Example: "W-w-what" (clear sound repetition)
                     - Example: [block: word] (clear blocking moment)
                  
                  3. Speech Markers to Use Instead:
                     - [pause] for natural pauses
                     - [thinking] for contemplative moments
                     - [emphasized] for stressed words
                     - [trailing off] for voice fading
                     - ... for short pauses
                     - ...... for longer pauses

                  CRITICAL: If you're not 100% certain it's a stutter, DO NOT mark it as one. Default to regular speech pattern markers.
                * **Pauses/Timing:**  ... (short), ...... (long), [pause].  Note changes in pace: [fast], [slow], [accelerating], [decelerating].
                * **Volume/Emphasis:** [quiet], [loud], [whispering], [shouting], [emphasized].
                * **Tone/Inflection:** [sarcastic tone], [questioning tone], [upspeak], [monotone].
                * **Non-verbal Sounds:** [laughs], [chuckles], [cries], [sighs], [breath], [deep breath], [throat-clear], [coughs].
                * **Voice Quality:** [shaky], [clear], [trembling], [nasal], [breathy], [strained], [raspy].


                **2. Communication Analysis:**
                As a communication coach, provide one specific piece of actionable advice or positive feedback based on the *transcription*. Focus on a single aspect that the speaker could improve or that they did particularly well. Keep it brief, friendly, and conversational. Begin with "Communication Tip:".

                **3. Conversational Response:**
                Respond to the *transcribed message* in a natural, conversational way, as if you were engaging in a casual dialogue with the speaker.  Your response should be relevant to the content of the transcription and maintain a friendly and engaging tone.

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
            
            # Validating that we have content
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