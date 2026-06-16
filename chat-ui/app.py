"""
Chat UI backend.

This Flask app is the "MCP client" sitting between the browser and the
MCP server. When the user submits a prompt:

  Browser  --(HTTP POST /chat)-->  Flask app
  Flask app --(MCP protocol)-->    MCP server  --(query)-->  MongoDB
                                    MCP server  --(prompt)--> Ollama
  Flask app  <--(tool result)--    MCP server
  Browser  <--(JSON response)--   Flask app

Every exchange is also logged to MongoDB's `chat_history` collection via
the MCP server's own logging (inside ask_healthcare_llm), so nothing here
needs to write to Mongo directly.
"""

import os
import asyncio
import time
from flask import Flask, render_template, request, jsonify
from mcp import ClientSession
from mcp.client.sse import sse_client

app = Flask(__name__)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000/sse")


async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Open a fresh MCP session, call one tool, return its text result."""
    async with sse_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            # MCP tool results are a list of content blocks; we only use text ones
            text_parts = [c.text for c in result.content if hasattr(c, "text")]
            return "\n".join(text_parts) if text_parts else "[No text response]"


def run_async(coro):
    """Flask routes are sync; this runs an async MCP call inside them."""
    return asyncio.run(coro)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_prompt = (data.get("prompt") or "").strip()
    context_limit = int(data.get("context_limit", 8))

    if not user_prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    start = time.time()
    try:
        response_text = run_async(
            call_mcp_tool(
                "ask_healthcare_llm",
                {"user_prompt": user_prompt, "context_limit": context_limit},
            )
        )
        elapsed_ms = int((time.time() - start) * 1000)
        return jsonify({
            "response": response_text,
            "latency_ms": elapsed_ms,
        })
    except Exception as e:
        return jsonify({"error": f"MCP call failed: {str(e)}"}), 500


@app.route("/status")
def status():
    try:
        result = run_async(call_mcp_tool("check_database_status", {}))
        return jsonify({"mcp_connected": True, "db_status": result})
    except Exception as e:
        return jsonify({"mcp_connected": False, "error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
