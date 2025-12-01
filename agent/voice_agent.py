import logging
import asyncio
import os
from dotenv import load_dotenv
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.llm import function_tool
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,  
    
)
from livekit.plugins import google
from rag_system import RAGSystem  
load_dotenv()
logger = logging.getLogger("gemini-agent")
logger.setLevel(logging.INFO)

rag = RAGSystem()


async def entrypoint(ctx: JobContext):
    logger.info("Starting Gemini Voice Agent")
    
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info("Connected to room")

    logger.info("Initializing Gemini model")
    model = google.beta.realtime.RealtimeModel(
        model="gemini-live-2.5-flash-preview",  
        voice="Aoede", 
    )
    logger.info("model initialized")

    @function_tool
    async def lookup_company_info(query: str):
        """
        Searches the company's FAQ database for information.
        Args:
            query: The user's question or keywords to search for
        """
        logger.info(f"Tool called with query: {query}")
        
      
        return rag.get_context(query)
    agent = Agent(
        instructions=(
            "You are a helpful customer support assistant. Answer questions using ONLY the knowledge base.\n"
            "\n"
            "RULES:\n"
            "1. ALWAYS use lookup_company_info tool for any company question\n"
            "2. Answer ONLY with information from the tool results - never improvise\n"
            "3. If no info found, say: 'I don't have that information. Please contact support.'\n"
            "4. For personal/account questions, say: 'I can't access specific account info. Please contact support.'\n"
            "5. For off-topic questions, redirect to company topics\n"
        ),
        tools=[lookup_company_info],
    )
    logger.info("Agent created")

    # 4. Start session
    logger.info("Starting session")
    session = AgentSession(
        llm=model,
    )

    await session.start(agent, room=ctx.room)
    
    logger.info("=" * 60)
    logger.info("✅ Agent is LIVE and ready!")
    logger.info("=" * 60)
    
    # 5. GREETING
    await asyncio.sleep(1)
    await session.generate_reply(
        instructions="Greet the user warmly and introduce yourself as a helpful assistant who can answer questions."
    )
    logger.info("Greeting sent")


if __name__ == "__main__":
   
    required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "GOOGLE_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]
    
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        logger.error("Add these to your .env file:")
        logger.error("  - Get Google API key: https://aistudio.google.com/apikey")
        logger.error("  - Get LiveKit creds: https://cloud.livekit.io/")
        exit(1)
    
    logger.info("✅ Environment loaded")
    logger.info(f"LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    logger.info("")
    
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


