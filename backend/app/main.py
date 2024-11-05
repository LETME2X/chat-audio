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

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

def process_audio_data(audio_base64: str) -> bytes:
    """Convert base64 audio data to bytes."""
    try:
        # Remove the data URL prefix if present
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
    """Process audio with Gemini Flash model - Three parts: transcription, analysis, and response"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # First: Get transcription
        transcription_response = await get_transcription(audio_bytes, model)
        transcription = transcription_response.text.strip() if transcription_response else None

        if transcription:
            # Second: Get communication feedback (brief and casual)
            analysis_prompt = f"""As a friendly communication coach, give a quick, casual tip about this message: "{transcription}"
            Keep it very brief (1-2 sentences) and conversational, like you're giving friendly advice to a friend.
            Start with "Communication Tip:" and focus on one specific aspect they did well or could improve."""
            
            analysis_response = model.generate_content(analysis_prompt, stream=False)
            analysis = analysis_response.text.strip() if analysis_response else None

            # Third: Generate conversational response
            conversation_prompt = f"""You are having a friendly chat. The person said: "{transcription}"
            Respond naturally and conversationally, as if you're just having a normal chat."""
            
            conversation_response = model.generate_content(conversation_prompt, stream=False)
            ai_reply = conversation_response.text.strip() if conversation_response else None

            return {
                'transcription': transcription,
                'analysis': analysis,
                'reply': ai_reply
            }
        return None

    except Exception as e:
        print(f"✗ Error processing with Gemini: {str(e)}")
        return None

async def get_transcription(audio_bytes, model):
    """Get transcription with emotions and speech patterns, focusing on stuttering"""
    try:
        transcription_prompt = [
            {
                "text": """Transcribe this audio with emotions and speech patterns:

                1. Emotions & Tone:
                - Basic: [happy] [sad] [excited] [calm] [angry] [nervous] [curious] [thoughtful]
                - Additional: [confident] [shy] [confused] [surprised] [worried] [playful]
                - Intensity: Can add [very] or [slightly] before emotion

                2. Stuttering Types (Mark as [stutter]):
                - Sound Repetitions: "b-b-book", "s-s-sorry"
                - Word Repetitions: "I- I mean", "what- what is"
                - Blocks: "...(trying to say)... hello"
                - Sound Prolongations: "ssssorry", "mmmmom"
                - Broken Words: "ta...ble", "comp...uter"

                3. Other Speech Patterns:
                - Volume: [whispering] [shouting]
                - Style: [singing] [rushing] [mumbling]
                - Sounds: [laughing] [sighing]
                - Gaps: [pausing] for "..."

                Rules:
                - Can combine patterns: [happy, laughing]
                - Mark tone changes as they occur
                - Write stutters exactly as heard
                - Include pauses in stuttered speech
                
                Examples:
                "[nervous, stutter] H-h-hi there [gaining confidence] how are you?"
                "[happy, singing] Hello! [excited, laughing] This is fun!"
                "[thoughtful, pausing] Well... [stutter] I-I think so"
                """
            },
            {
                "inline_data": {
                    "mime_type": "audio/wav",
                    "data": base64.b64encode(audio_bytes).decode('utf-8')
                }
            }
        ]
        return model.generate_content(transcription_prompt, stream=False)
    except Exception as e:
        print(f"✗ Error getting transcription: {str(e)}")
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
                    result = await process_audio_with_gemini(audio_bytes)
                    
                    if result:
                        await websocket.send_json({
                            'type': 'transcription',
                            'text': result['transcription'],
                            'analysis': result['analysis']
                        })
                        
                        # Store user's message
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
                        
                        if result['reply']:
                            await websocket.send_json({
                                'type': 'ai_reply',
                                'text': result['reply']
                            })
                            
                            # Store AI reply
                            await store_message({
                                'user_id': data.get('userId'),
                                'temp_user_id': data.get('tempUserId'),
                                'message': result['reply'],
                                'is_ai': True,
                                'session_type': 'logged-in' if data.get('userId') else 'temporary',
                                'status': STATUS['SUCCESS'],
                                'reply': result['reply']
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