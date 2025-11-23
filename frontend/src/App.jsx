/**
 * Voice Agent Frontend - FINAL WORKING VERSION
 * Uses available LiveKit components with proper error handling
 */

import React, { useState, useEffect } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useRoomContext,
  useTracks,
  useParticipants,
  ControlBar,
  DisconnectButton,
} from '@livekit/components-react';
import { Track } from 'livekit-client';
import '@livekit/components-styles';
import './App.css';


function App() {
  const [token, setToken] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState('');

  const handleConnect = async () => {
    setConnecting(true);
    setError('');
    
    try {
      console.log('Attempting to connect to token server...');
      
      // Get token from backend
      const response = await fetch('http://localhost:8080/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room: 'voice-agent-room',
          identity: 'user-' + Math.random().toString(36).substring(7),
        }),
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server error:', errorText);
        throw new Error(`Server returned ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('Received token, connecting to room...');
      
      setToken(data.token);
      setConnecting(false);
      
    } catch (err) {
      console.error('Connection error:', err);
      
      let errorMessage = 'Failed to connect. ';
      
      if (err.message.includes('Failed to fetch')) {
        errorMessage += 'Cannot reach token server on port 8080. Make sure "python token_server.py" is running.';
      } else {
        errorMessage += err.message;
      }
      
      setError(errorMessage);
      setConnecting(false);
    }
  };

  const handleDisconnect = () => {
    setToken('');
    setConnecting(false);
    setError('');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎤 LiveKit Voice Agent</h1>
        <p>Powered by Gemini Live API + RAG</p>
      </header>

      <main className="App-main">
        {!token ? (
          /* Connection Screen */
          <div className="connect-section">
            <div className="info-card">
              <h2>Connect to Voice Agent</h2>
              <p>Join a LiveKit room where the AI voice agent is running.</p>
              
              <ul className="features">
                <li>🎙️ Real-time voice interaction via LiveKit</li>
                <li>🤖 Gemini Live API for natural speech</li>
                <li>📚 RAG-powered accurate answers from knowledge base</li>
                <li>⚡ Low-latency WebRTC audio streaming</li>
              </ul>
            </div>

            {error && (
              <div className="error-box">
                <strong>❌ Error:</strong><br />
                {error}
              </div>
            )}

            <button
              className="connect-button"
              onClick={handleConnect}
              disabled={connecting}
            >
              {connecting ? '⏳ Connecting...' : '🔗 Connect to Agent'}
            </button>

            <div className="instructions">
              <h3>💡 Try asking:</h3>
              <ul>
                <li>"What are your business hours?"</li>
                <li>"How can I contact support?"</li>
                <li>"What products do you offer?"</li>
                <li>"Is my data secure?"</li>
                <li>"What payment methods do you accept?"</li>
              </ul>
            </div>

            <div className="setup-note">
              <h4>⚠️ Make sure these are running:</h4>
              <ol>
                <li>
                  <strong>Terminal 1 - LiveKit Agent:</strong><br />
                  <code>python agent/livekit_gemini_agent.py dev</code><br />
                  Should show: "registered worker"
                </li>
                <li>
                  <strong>Terminal 2 - Token Server:</strong><br />
                  <code>python token_server.py</code><br />
                  Should show: "Server: http://localhost:8080"
                </li>
                <li>
                  <strong>Test token server:</strong><br />
                  Open <a href="http://localhost:8080/health" target="_blank">http://localhost:8080/health</a><br />
                  Should return: {`{"status":"ok"}`}
                </li>
              </ol>
            </div>
          </div>
        ) : (
          /* LiveKit Room */
          <LiveKitRoom
            serverUrl={process.env.REACT_APP_LIVEKIT_URL || 'wss://voice-agent-ji4ta3qq.livekit.cloud'}
            token={token}
            connect={true}
            audio={true}
            video={false}
            onDisconnected={handleDisconnect}
            onError={(error) => {
              console.error('LiveKit error:', error);
              setError(`LiveKit error: ${error.message}`);
            }}
            className="livekit-room"
          >
            <RoomContent />
          </LiveKitRoom>
        )}
      </main>

      <footer className="App-footer">
        <p>Built with LiveKit Agents + Gemini Live API + RAG</p>
      </footer>
    </div>
  );
}


/**
 * Content inside LiveKit Room
 */
function RoomContent() {
  const room = useRoomContext();
  const participants = useParticipants();
  const tracks = useTracks([Track.Source.Microphone]);
  
  const [status, setStatus] = useState('connecting');
  const [agentInfo, setAgentInfo] = useState(null);

  useEffect(() => {
    if (room) {
      console.log('Room state:', room.state);
      console.log('Room name:', room.name);
      
      if (room.state === 'connected') {
        setStatus('connected');
        console.log('✅ Connected to LiveKit room');
      } else if (room.state === 'disconnected') {
        setStatus('disconnected');
      }
    }
  }, [room, room?.state]);

  useEffect(() => {
    console.log('Participants:', participants.length);
    participants.forEach(p => {
      console.log('- Participant:', p.identity, p.isSpeaking ? '(speaking)' : '');
    });
    
    // Find agent participant
    const agent = participants.find(p => 
      p.identity && (
        p.identity.toLowerCase().includes('agent') || 
        p.identity.toLowerCase().includes('voice') ||
        p.identity.startsWith('AW_')
      )
    );
    
    if (agent) {
      setAgentInfo({
        identity: agent.identity,
        isSpeaking: agent.isSpeaking,
        hasAudio: agent.audioTracks.size > 0
      });
      console.log('✅ Agent found:', agent.identity);
    } else {
      setAgentInfo(null);
    }
  }, [participants]);

  return (
    <div className="voice-interface">
      <div className="status-card">
        <h2>🎙️ Voice Session Active</h2>
        
        <div className={`status-indicator ${status}`}>
          <span className="status-dot"></span>
          <span className="status-text">
            {status === 'connecting' && '🔗 Connecting to room...'}
            {status === 'connected' && '✅ Connected - Ready to talk!'}
            {status === 'disconnected' && '❌ Disconnected'}
          </span>
        </div>

        <div className="room-info">
          <p><strong>Room:</strong> {room.name}</p>
          <p><strong>Your ID:</strong> {room.localParticipant?.identity}</p>
          <p><strong>Total Participants:</strong> {participants.length}</p>
          {agentInfo && (
            <>
              <p><strong>Agent ID:</strong> {agentInfo.identity}</p>
              {agentInfo.isSpeaking && <p className="speaking">🗣️ Agent is speaking</p>}
              {agentInfo.hasAudio && <p className="has-audio">🔊 Agent audio available</p>}
            </>
          )}
        </div>
      </div>

      {/* Microphone Status */}
      <div className="mic-section">
        <h3>🎤 Your Microphone</h3>
        {tracks.length > 0 ? (
          <div className="mic-active">
            ✅ Microphone Active
            <p className="mic-note">
              The agent will automatically hear you when you speak.<br />
              Voice Activity Detection (VAD) is enabled.
            </p>
          </div>
        ) : (
          <div className="mic-inactive">
            ⚠️ Microphone Not Detected
            <p className="mic-note">
              Check browser permissions: Click the 🔒 icon in address bar → Allow microphone
            </p>
          </div>
        )}
      </div>

      {/* Agent Info */}
      <div className="agent-info">
        <h3>🤖 AI Agent Status</h3>
        {agentInfo ? (
          <div className="agent-active">
            ✅ Agent is in the room and listening
            <p className="agent-note">
              <strong>How it works:</strong><br />
              • Agent uses <strong>Gemini Live API</strong> for speech processing<br />
              • <strong>RAG</strong> searches the knowledge base for accurate answers<br />
              • Responds with natural voice synthesis<br />
              • No buttons needed - just speak naturally!
            </p>
          </div>
        ) : (
          <div className="agent-waiting">
            ⏳ Waiting for agent to join room...
            <p className="agent-note">
              <strong>Make sure agent is running:</strong><br />
              In Terminal 1, run:<br />
              <code>python agent/voice_agent.py dev</code><br />
              <br />
              Should see: "registered worker" and "waiting for job"
            </p>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="controls">
        <ControlBar 
          controls={{
            microphone: true,
            camera: false,
            screenShare: false,
          }}
        />
        
        <DisconnectButton className="disconnect-btn">
          Leave Session
        </DisconnectButton>
      </div>

      {/* Audio Renderer - Plays agent's voice */}
      <RoomAudioRenderer />

      {/* Instructions */}
      <div className="instructions-box">
        <h3>💡 How to use:</h3>
        <ol>
          <li>✅ Check that your microphone is active (green checkmark above)</li>
          <li>⏳ Wait for the AI agent to join the room</li>
          <li>🗣️ Simply start speaking your question naturally</li>
          <li>👂 The agent will automatically detect your voice and respond</li>
          <li>💬 Have a natural conversation - no buttons to press!</li>
        </ol>
      </div>

      {/* Knowledge Base Topics */}
      <div className="knowledge-info">
        <h4>📚 Topics the agent knows about (via RAG):</h4>
        <div className="topics">
          <span className="topic">Business Hours</span>
          <span className="topic">Customer Support</span>
          <span className="topic">Products & Services</span>
          <span className="topic">Return Policy</span>
          <span className="topic">Training Programs</span>
          <span className="topic">Payment Methods</span>
          <span className="topic">Data Security</span>
          <span className="topic">Plan Management</span>
        </div>
      </div>
    </div>
  );
}


export default App;