import asyncio
import sys
import os

# Ensure we can import mcp
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    # Path to server.py
    server_script = os.path.join(os.path.dirname(__file__), "server.py")
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=os.environ.copy()
    )

    print(f"Connecting to server at: {server_script}")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"Tools available: {[t.name for t in tools.tools]}")

            # Call search_deeds
            print("\nCalling search_deeds with owner_name='Smith'...")
            try:
                result = await session.call_tool("search_deeds", arguments={"owner_name": "Smith"})
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error calling tool: {e}")

if __name__ == "__main__":
    asyncio.run(run())
