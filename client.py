
import asyncio
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

load_dotenv()


def resolve_model_name():
    """Return the GROQ model name from environment or a sensible default."""
    model = os.getenv("GROQ_MODEL")
    if model:
        return model
    return "llama-3.1-8b-instant"


# -----------------------------------------
# MCP Tool Logging Interceptor
# -----------------------------------------

async def logging_interceptor(request, handler):
    print("\n" + "=" * 50)
    print("[CLIENT] MCP TOOL CALL")
    print(f"[CLIENT] Tool Name: {request.name}")
    print(f"[CLIENT] Arguments: {request.args}")
    print("=" * 50)

    try:
        result = await handler(request)

        print("[CLIENT] MCP TOOL RESULT")
        print(f"[CLIENT] Result: {result}")
        print("=" * 50)

        return result

    except Exception as e:
        print("[CLIENT] MCP TOOL ERROR")
        print(f"[CLIENT] Error: {e}")
        print("=" * 50)
        raise


# -----------------------------------------
# Main Application
# -----------------------------------------

async def main():

    # 1. Validate API Key
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError(
            "GROQ_API_KEY is missing. Please set it in .env"
        )

    # 2. Create Groq Model
    model = ChatGroq(
        model=resolve_model_name(),
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    # 3. Connect to MCP Server
    client = MultiServerMCPClient(
        {
            "calculator": {
                "transport": "streamable_http",
                "url": "http://127.0.0.1:8001/mcp",
            }
        },
        tool_interceptors=[logging_interceptor],
    )

    # 4. Load MCP Tools
    tools = await client.get_tools()

    print("\n[MCP] Available tools:")

    for tool in tools:
        print(f"- {tool.name}")

    # 5. Create LangChain Agent
    agent = create_agent(
        model,
        tools,
    )

    print("\n" + "=" * 50)
    print("Calculator Chatbot Started")
    print("Type 'exit' to quit")
    print("=" * 50)

    # 6. Continuous User Input Loop
    while True:

        user_input = input("\nYou: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:

            print("\n[AGENT] Processing your question...")

            # 7. Send Dynamic User Prompt
            response = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_input,
                        }
                    ]
                }
            )

            # 8. Print Final Response
            final_message = response["messages"][-1]

            print("\nAssistant:")

            if isinstance(final_message.content, str):
                print(final_message.content)
            else:
                print(final_message.content)

        except Exception as e:

            print("\n[ERROR]")
            print(str(e))


if __name__ == "__main__":
    asyncio.run(main())