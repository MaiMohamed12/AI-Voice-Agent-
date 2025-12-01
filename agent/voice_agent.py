import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.llm import function_tool
from livekit.plugins import google
from rag_system import RAGSystem

load_dotenv()
logger = logging.getLogger("gemini-agent")
rag = RAGSystem()
async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # 1. DEFINE THE MODEL (The "General" Brain)
    model = google.beta.realtime.RealtimeModel(
        model="gemini-live-2.5-flash-preview",
        voice="Aoede",
    )

    
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
            "You are a helpful company FAQ assistant. Your role is to answer general questions about "
        "company policies, services, and procedures using ONLY the FAQ database.\n"
        "\n"
        "CRITICAL RULES - READ CAREFULLY:\n"
        "1. You ONLY have access to general FAQ information - you CANNOT access specific customer data, "
        "order details, account information, or any personal or transactional data.\n"
        "\n"
        "2. ALWAYS use the lookup_company_info tool for ANY question about company policies or procedures.\n"
        "\n"
        "3. ANSWER ONLY WITH INFORMATION FROM THE RETRIEVED FAQ DATA:\n"
        "   - DO NOT use your training data or general knowledge\n"
        "   - DO NOT improvise or add information not in the FAQ results\n"
        "   - DO NOT infer or assume anything beyond what's explicitly stated in the FAQ\n"
        "\n"
        "4. If the lookup_company_info tool returns no relevant information, "
        "you MUST respond: 'I don't have that information in my FAQ database. Please contact our support team for help.'\n"
        "\n"
        "5. If a user asks about personal, private, or specific account-related information, "
        "politely explain that you only provide general FAQ information and they should contact support.\n"
        "\n"
        "6. NEVER ask for sensitive personal information.\n"
        "\n"
        "7. If a question is unrelated to the company or its services, "
        "respond: 'I can only help with questions related to our company services and policies.'\n"
        "\n"
        "REMEMBER: You are a STRICT FAQ assistant. Only repeat information from the FAQ database. "
        "Never add, infer, or improvise information."
        ),
        tools=[lookup_company_info],
    )

    # 4. START THE SESSION
    session = AgentSession(
        llm=model,
    )

    await session.start(agent, room=ctx.room)
    
    # 5. GREETING
    await asyncio.sleep(1)
    session.generate_reply(instructions="Greet the user warmly and introduce yourself as a helpful assistant who can answer questions.")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))