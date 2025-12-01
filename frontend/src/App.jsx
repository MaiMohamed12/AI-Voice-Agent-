/**
 * Voice Agent Frontend - WITH LIVE TRANSCRIPT
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useRoomContext,
  useTracks,
  useParticipants,
  ControlBar,
  DisconnectButton,
} from '@livekit/components-react';
import { Track, RoomEvent } from 'livekit-client'; // Added RoomEvent
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
      // Get token from backend
      const response = await fetch('http://localhost:8080/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room: 'voice-agent-room',
          identity: 'user-' + Math.random().toString(36).substring(7),
        }),
      });

      if (!response.ok) throw new Error(`Server returned ${response.status}`);
      const data = await response.json();
      setToken(data.token);
      setConnecting(false);
      
    } catch (err) {
      console.error('Connection error:', err);
      setError('Failed to connect. Make sure token_server.py is running.');
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
        <h1>LiveKit Voice Agent</h1>
      </header>

      <main className="App-main">
        {!token ? (
          <div className="connect-section">
            <div className="info-card">
              <h2>Connect to Voice Agent</h2>
              <p>Join to start the voice interaction.</p>
            </div>
            {error && <div className="error-box">{error}</div>}
            <button className="connect-button" onClick={handleConnect} disabled={connecting}>
              {connecting ? '⏳ Connecting...' : '🔗 Connect to Agent'}
            </button>
          </div>
        ) : (
          <LiveKitRoom
            serverUrl={process.env.REACT_APP_LIVEKIT_URL || 'wss://voice-agent-ji4ta3qq.livekit.cloud'}
            token={token}
            connect={true}
            audio={true}
            video={false}
            onDisconnected={handleDisconnect}
            className="livekit-room"
          >
            <RoomContent />
          </LiveKitRoom>
        )}
      </main>
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
  const [transcripts, setTranscripts] = useState([]); // State for transcripts
  const messagesEndRef = useRef(null); // To auto-scroll

  // Scroll to bottom when new message arrives
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [transcripts]);

  // Handle Room Status
  useEffect(() => {
    if (room) {
      if (room.state === 'connected') setStatus('connected');
      else if (room.state === 'disconnected') setStatus('disconnected');
    }
  }, [room, room?.state]);

  // --- LIVE TRANSCRIPT LOGIC ---
  useEffect(() => {
    if (!room) return;

    const onTranscription = (segments, participant, publication) => {
      const segment = segments[0];
      // Only record final segments to avoid jittery partial updates
      if (!segment || !segment.final) return;

      const text = segment.text;
      const isAgent = participant?.identity?.toLowerCase().includes('agent') || 
                      participant?.identity?.startsWith('AW_');

      setTranscripts(prev => [...prev, {
        id: segment.id,
        text: text,
        sender: isAgent ? 'Agent' : 'You',
        isAgent: isAgent,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    };

    // Listen for transcription events
    room.on(RoomEvent.TranscriptionReceived, onTranscription);

    // Cleanup listener
    return () => {
      room.off(RoomEvent.TranscriptionReceived, onTranscription);
    };
  }, [room]);

  return (
    <div className="voice-interface">
      <div className="status-card">
        <div className={`status-indicator ${status}`}>
          <span className="status-dot"></span>
          <span className="status-text">
            {status === 'connected' ? '✅ Connected' : '🔗 Connecting...'}
          </span>
        </div>
      </div>

      {/* --- NEW TRANSCRIPT SECTION --- */}
      <div className="transcript-section">
        <h3>💬 Live Transcript</h3>
        <div className="transcript-container">
          {transcripts.length === 0 && (
            <div className="empty-state">Start speaking to see the conversation...</div>
          )}
          
          {transcripts.map((msg, idx) => (
            <div key={idx} className={`message ${msg.isAgent ? 'agent-msg' : 'user-msg'}`}>
              <div className="msg-header">
                <span className="sender">{msg.sender}</span>
                <span className="time">{msg.timestamp}</span>
              </div>
              <div className="msg-content">{msg.text}</div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Mic Status */}
      <div className="mic-status-mini">
        {tracks.length > 0 ? '🎤 Mic Active' : '🔇 Mic Missing'}
      </div>

      {/* Controls */}
      <div className="controls">
        <ControlBar controls={{ microphone: true, camera: false, screenShare: false }} />
        <DisconnectButton className="disconnect-btn">Disconnect</DisconnectButton>
      </div>

      <RoomAudioRenderer />
    </div>
  );
}

export default App;