"""
test_mcp_client.py
A minimal MCP client to verify the server's tools actually work end-to-end.

Run this directly on the VM (not inside a container):
    pip3 install mcp --break-system-packages
    python3 scripts/test_mcp_client.py
"""

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_SERVER_URL = "http://localhost:8000/sse"


async def main():
    print(f"Connecting to MCP server at {MCP_SERVER_URL} ...")

    async with sse_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected and initialized.\n")

            # ── List available tools ──────────────────────────
            tools_result = await session.list_tools()
            print("Available tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description.strip().splitlines()[0]}")
            print()

            # ── Test 1: database status check ─────────────────
            print("── Test 1: check_database_status ──")
            result = await session.call_tool("check_database_status", {})
            print(result.content[0].text)
            print()

            # ── Test 2: list a few patients ───────────────────
            print("── Test 2: list_all_patients(limit=3) ──")
            result = await session.call_tool("list_all_patients", {"limit": 3})
            print(result.content[0].text)
            print()

            # ── Test 3: ask the LLM directly through the tool ─
            print("── Test 3: ask_healthcare_llm ──")
            print("Sending prompt: 'What is the standard treatment for hypertension?'")
            result = await session.call_tool(
                "ask_healthcare_llm",
                {"user_prompt": "What is the standard treatment for hypertension?"}
            )
            print("LLM response:")
            print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
