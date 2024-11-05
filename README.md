# Real-Time Audio Chat Application

## Project Overview
This application enables users to send audio messages and receive AI-powered responses in real-time. Users can start chatting anonymously and are prompted to log in with Google after 5 messages. The system uses WebSocket connections for real-time communication and integrates with Google's Gemini AI for message processing.

## Technical Stack
- **Frontend**: Next.js 14 with TypeScript
- **Backend**: FastAPI (Python)
- **Database**: Supabase
- **Authentication**: Supabase Google OAuth
- **AI Integration**: Google Gemini 1.5 Flash API
- **Real-time Communication**: WebSocket

## Prerequisites
- Node.js 18+
- Python 3.9+
- Supabase account
- Google Cloud account with Gemini API access
- Git

## Step-by-Step Setup Guide

### 1. Clone Repository
```bash
git clone <repository-url>
cd audio-chat



### 2. Supabase Database Setup

1. Create a new project at [Supabase](https://supabase.com).
2. Go to the **SQL Editor** in the Supabase dashboard.
3. Execute the following SQL commands:

```sql
-- 1. Create custom user profile table
CREATE TABLE user_profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE,
    temporary_sessions TEXT[]
);
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own profile"
    ON user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update their own profile"
    ON user_profiles FOR UPDATE USING (auth.uid() = id);

-- 2. Create messages table
CREATE TABLE messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    temp_user_id TEXT,
    message TEXT,
    transcription TEXT,
    analysis TEXT,
    reply TEXT,
    is_ai BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_type TEXT CHECK (session_type IN ('temporary', 'logged-in')),
    status TEXT DEFAULT 'pending',
    audio_url TEXT,
    audio_duration INTEGER,
    audio_format TEXT,
    processing_time FLOAT
);
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own messages"
    ON messages FOR SELECT
    USING ((auth.uid() = user_id) OR
    (temp_user_id IS NOT NULL AND
    temp_user_id = current_setting('app.temp_user_id', TRUE)));
CREATE POLICY "Users can insert messages"
    ON messages FOR INSERT
    WITH CHECK ((auth.uid() = user_id) OR (temp_user_id IS NOT NULL));

-- 3. Create session merges table
CREATE TABLE session_merges (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    temp_user_id TEXT NOT NULL,
    merged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed'))
);
ALTER TABLE session_merges ENABLE ROW LEVEL SECURITY;

-- 4. Create necessary indexes
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_temp_user_id ON messages(temp_user_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_session_merges_temp_user_id ON session_merges(temp_user_id);
CREATE INDEX idx_messages_session_type ON messages(session_type);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_user_profiles_last_seen ON user_profiles(last_seen);

-- 5. Create merge function
CREATE OR REPLACE FUNCTION merge_temporary_session(
    p_user_id UUID,
    p_temp_user_id TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO session_merges (user_id, temp_user_id)
    VALUES (p_user_id, p_temp_user_id);
    UPDATE messages
    SET user_id = p_user_id,
        session_type = 'logged-in',
        temp_user_id = NULL
    WHERE temp_user_id = p_temp_user_id;
    UPDATE session_merges
    SET status = 'completed'
    WHERE user_id = p_user_id AND temp_user_id = p_temp_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;



### 3. Backend Setup

1. Navigate to the backend directory:
    ```bash
    cd backend
    ```

2. Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # For Unix/macOS
    # OR
    venv\Scripts\activate     # For Windows
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create the `.env` file:
    ```bash
    cp .env.example .env
    ```

5. Update the `.env` file with your credentials:
    ```dotenv
    SUPABASE_URL=your_project_url
    SUPABASE_KEY=your_service_role_key
    GEMINI_API_KEY=your_gemini_api_key
    ```

### 4. Frontend Setup

1. Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2. Install dependencies:
    ```bash
    npm install
    ```

3. Create the `.env.local` file:
    ```bash
    cp .env.local.example .env.local
    ```


### 4. Update .env.local with your credentials:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=your_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key



5. Google Cloud Setup
1. Create a new project in Google Cloud Console.
2. Enable Gemini API.
3. Create API credentials.
4. Copy the API key to the backend `.env` file.



6. Running the Application

1. Start backend server:
cd backend
source venv/bin/activate  # For Unix/macOS
# OR
venv\Scripts\activate     # For Windows
uvicorn app.main:app --reload



2. Start frontend development server:
cd frontend
npm run dev


3. Access application:
http://localhost:3000



7. Testing the Application
1. Open http://localhost:3000 in your browser
2. Allow microphone access when prompted
3. Record and send an audio message
4. Verify transcription and AI response
5. Test anonymous chat (up to 5 messages)
6. Test Google authentication
7. Verify message persistence in Supabase


Features
- Real-time audio messaging
- Speech-to-text conversion
- AI-powered responses
- Anonymous chat with temporary sessions
- Google authentication
- Session merging after login
- Message persistence
- Real-time communication via WebSocket


Troubleshooting
1. If WebSocket connection fails:
   - Verify backend server is running
   - Check WebSocket URL in frontend .env.local
   - Ensure CORS settings are correct

2. If database operations fail:
   - Verify Supabase credentials
   - Check RLS policies
   - Verify table structures

3. If audio recording fails:
   - Check microphone permissions
   - Verify browser compatibility
   - Check console for errors



Security Considerations
- All sensitive credentials are stored in .env files
- Database access is protected by RLS policies
- WebSocket connections are authenticated
- Temporary sessions are properly managed
- User data is isolated and protected


Limitations
- Audio messages must be in WAV format
- Maximum 5 messages for anonymous users
- Basic error recovery for WebSocket disconnections
- Session merging is one-way only



Future Improvements
1. Support for more audio formats
2. Enhanced error handling
3. Two-way session merging
4. Rate limiting implementation
5. Offline message support




