```diff
--- a/README.md
+++ b/README.md
@@ -1,3 +1,5 @@
+# Real-Time Audio Chat Application
+
 ## Project Overview
 This application enables users to send audio messages and receive AI-powered responses in real-time. Users can start chatting anonymously and are prompted to log in with Google after 5 messages. The system uses WebSocket connections for real-time communication and integrates with Google's Gemini AI for message processing.
 
@@ -13,15 +15,17 @@
 - Google Cloud account with Gemini API access
 - Git
 
-## Step-by-Step Setup Guide
-
-### 1. Clone Repository
+## Setting up the Application
+
+### 1. Cloning the Repository
+
 ```bash
 git clone <repository-url>
 cd audio-chat
 
-
-```
+```
+
+### 2. Setting Up Supabase
 
 ### 2. Supabase Database Setup
 
@@ -106,7 +110,7 @@
 $$ LANGUAGE plpgsql SECURITY DEFINER;
 
 
-
+### 3. Setting Up the Backend
 ### 3. Backend Setup
 
 1. Navigate to the backend directory:
@@ -143,7 +147,7 @@
     cp .env.local.example .env.local
     ```
 
-
+### 4. Updating Credentials
 ### 4. Update .env.local with your credentials:
 
 ```dotenv
@@ -152,7 +156,7 @@
 NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
 
 
-### 5. Google Cloud Setup
+### 5. Setting Up Google Cloud
 1. Create a new project in Google Cloud Console.
 2. Enable Gemini API.
 3. Create API credentials.
@@ -160,30 +164,30 @@
 4. Copy the API key to the backend `.env` file.
 
 
-### 6. Running the Application
-
-#### 1. Start backend server:
-    
-    ```bash
+### 6. Running the Application
+
+#### 1. Starting the Backend Server
+
+```bash
     cd backend
 source venv/bin/activate  # For Unix/macOS
 # OR
 venv\Scripts\activate     # For Windows
     uvicorn app.main:app --reload
-    ```
-    
-#### 2. Start frontend development server:
-    
-    ```bash
+```
+
+#### 2. Starting the Frontend Development Server
+
+```bash
     cd frontend
 npm run dev
-    ```
-    
-#### 3. Access application:
-    
-    ```bash
+```
+
+#### 3. Accessing the Application
+
+```bash
 http://localhost:3000
-    ```
+
+```
     
 ### 7. Testing the Application
 1. Open http://localhost:3000 in your browser
@@ -194,30 +198,30 @@
 6. Test Google authentication
 7. Verify message persistence in Supabase
 
-
-### Features
+## Features
+
 - Real-time audio messaging
 - Speech-to-text conversion
 - AI-powered responses
 - Anonymous chat with temporary sessions
 - Google authentication
 - Session merging after login
 - Message persistence
 - Real-time communication via WebSocket
 
-
-### Troubleshooting
+## Troubleshooting
+
 1. If WebSocket connection fails:
    - Verify backend server is running
    - Check WebSocket URL in frontend .env.local
    - Ensure CORS settings are correct
 
 2. If database operations fail:
-   - Verify Supabase credentials
-   - Check RLS policies
-   - Verify table structures
+    - Verify Supabase credentials
+    - Check RLS policies
+    - Verify table structures
 
 3. If audio recording fails:
    - Check microphone permissions
@@ -225,8 +229,8 @@
    - Check console for errors
 
 
-
-### Security Considerations
+## Security Considerations
+
 - All sensitive credentials are stored in .env files
 - Database access is protected by RLS policies
 - WebSocket connections are authenticated
@@ -235,8 +239,8 @@
 - User data is isolated and protected
 
 
-### Limitations
+## Limitations
 
 - Audio messages must be in WAV format
 - Maximum 5 messages for anonymous users
@@ -245,7 +249,7 @@
 - Session merging is one-way only
 
 
-### Future Improvements
+## Future Improvements
 1. Support for more audio formats
 2. Enhanced error handling
 3. Two-way session merging

```
