from .supabase import supabase  # Import the single supabase instance
import uuid

async def set_temp_user_id(temp_id: str):
    """Set temporary user ID in database session"""
    try:
        supabase.rpc('set_temp_user_id', {'temp_id': temp_id}).execute()
    except Exception as e:
        print(f"✗ Error setting temp user ID: {str(e)}")

async def store_message(data: dict):
    """Helper function to store messages in Supabase"""
    try:
        status = data.get('status', 'received')
        temp_user_id = data.get('temp_user_id')
        
        # Set temp_user_id in session if provided
        if temp_user_id:
            await set_temp_user_id(temp_user_id)
            
            # Ensure temp_user_id exists in 'temporary_users' table
            response = supabase.table('temporary_users').select('id').eq('id', temp_user_id).execute()
            if not response.data:
                # Insert temp_user_id into 'temporary_users' table
                insert_response = supabase.table('temporary_users').insert({'id': temp_user_id}).execute()
                if insert_response.error:
                    print(f"✗ Error inserting temp_user_id into temporary_users: {insert_response.error}")
                    return {"error": insert_response.error.message}
        
        message_data = {
            'message': data.get('message', ''),
            'is_ai': data.get('is_ai', False),
            'session_type': data.get('session_type', 'temporary'),
            'status': status,
            'temp_user_id': temp_user_id,
            'user_id': data.get('user_id'),
            'audio_url': data.get('audio_url'),
            'audio_duration': data.get('audio_duration'),
            'audio_format': data.get('audio_format', 'wav'),
            'transcription': data.get('transcription'),
            'analysis': data.get('analysis'),
            'reply': data.get('reply'),
            'processing_time': data.get('processing_time')
        }
        
        if 'audio_url' in data:
            message_data['audio_url'] = data['audio_url']
        if 'processing_time' in data:
            message_data['processing_time'] = data['processing_time']
            
        response = supabase.table('messages').insert(message_data).execute()
        if response.error:
            print(f"✗ Database error inserting message: {response.error}")
            return {"error": response.error.message}
        return response.data
    except Exception as e:
        print(f"✗ Database error: {str(e)}")
        return {"error": str(e)}

async def merge_sessions(temp_user_id: str, user_id: str):
    """Merge temporary session into logged-in user session"""
    try:
        # Start transaction
        async with supabase.pool.acquire() as connection:
            async with connection.transaction():
                # Update messages
                await connection.execute("""
                    UPDATE messages 
                    SET user_id = $1, 
                        temp_user_id = NULL,
                        session_type = 'logged-in'
                    WHERE temp_user_id = $2
                """, user_id, temp_user_id)
                
                # Create merge record
                await connection.execute("""
                    INSERT INTO session_merges (user_id, temp_user_id, status)
                    VALUES ($1, $2, 'completed')
                """, user_id, temp_user_id)
                
        return {"success": True}
    except Exception as e:
        print(f"✗ Error merging sessions: {str(e)}")
        return {"error": str(e)}

def generate_temp_user_id():
    """Generate a unique temporary user ID"""
    return f"temp_{str(uuid.uuid4())}"