# Voice AI Agent
*A real-time voice AI that answers questions from a knowledge base.*
## How It Works

    You speak → LiveKit Cloud → Gemini AI                                                               
     → Searches your FAQs → Speaks  answer back                                                                 

Here's the magic: When you ask "What are your business hours?", the system:

1. Hears you speak through your microphone
2. Sends your voice to Gemini (Google's AI)
3. Gemini understands your question
4. Searches your knowledge base for the answer
5. Speaks the answer back to you naturally


## Quick Setup
### Get API Keys 
### Google Gemini:

1. Visit aistudio.google.com/apikey
2. Click "Get API Key"
3. Copy the key (starts with AIza...)

### LiveKit:

1. Sign up at cloud.livekit.io
2. Create a new project
3. Go to Settings → Keys
4. Copy: API Key, API Secret, WebSocket URL
### Create .env file:
```
GOOGLE_API_KEY=your_google_key_here
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

```

### Install packages:
```
pip install livekit livekit-agents livekit-plugins-google python-dotenv flask flask-cors sentence-transformers faiss-cpu

cd frontend
npm install
```
## Run It
*Open 3 terminals:*
### Terminal 1:
```
python voice_agent.py dev
```
You will see "registered worker"
### Terminal 2:
```
python token_server.py
```
You will see "Server: http://localhost:8080"
### Terminal 3:
```
cd frontend
npm start
```
Opens browser to localhost:3000
## Use It

1. Click "Connect to Agent"
2. Allow microphone
3. Wait for "Agent is in the room"
4. Start talking!

## Try asking:
- "What are your business hours?"
- "How can I contact support?"
- "Is my data secure?"
  
























