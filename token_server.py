"""
LiveKit Token Server - FIXED VERSION
Port 8080 - Generates access tokens for clients
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from livekit import api
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# LiveKit credentials
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")

if not all([LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL]):
    logger.error("❌ Missing LiveKit credentials!")
    logger.error("   Required: LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL")
    exit(1)


@app.route('/token', methods=['POST', 'OPTIONS'])
def create_token():
    """
    Generate LiveKit access token for a user
    
    Request body:
        {
            "room": "room-name",
            "identity": "user-identity"
        }
    
    Response:
        {
            "token": "eyJhbGc...",
            "url": "wss://..."
        }
    """
    # Handle preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json or {}
        room_name = data.get('room', 'voice-agent-room')
        identity = data.get('identity', 'user-' + os.urandom(4).hex())
        
        logger.info(f"🎟️  Generating token for {identity} in room {room_name}")
        
        # Create access token
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(identity)
        token.with_name(identity)
        
        # Grant permissions
        token.with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        
        # Generate JWT
        jwt_token = token.to_jwt()
        
        logger.info(f"✅ Token generated for {identity}")
        
        response = jsonify({
            'token': jwt_token,
            'url': LIVEKIT_URL,
        })
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error generating token: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'livekit_url': LIVEKIT_URL,
        'service': 'token-server',
        'port': 8080
    })


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'LiveKit Token Server',
        'endpoints': {
            'POST /token': 'Generate access token',
            'GET /health': 'Health check'
        }
    })


if __name__ == '__main__':
    logger.info("\n" + "="*60)
    logger.info("🎟️  LiveKit Token Server")
    logger.info("="*60)
    logger.info(f"📡 LiveKit URL: {LIVEKIT_URL}")
    logger.info(f"🔑 API Key: {LIVEKIT_API_KEY[:10]}...")
    logger.info(f"\n🌐 Server: http://localhost:8080")
    logger.info(f"🎯 Endpoint: POST /token")
    logger.info(f"🏥 Health: GET /health")
    logger.info("")
    logger.info("="*60 + "\n")
    
    # Run on port 8080
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=True)