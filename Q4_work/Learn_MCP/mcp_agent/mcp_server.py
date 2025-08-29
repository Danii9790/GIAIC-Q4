import json
from mcp.server.fastmcp import FastMCP
import requests

# --- 1. Create and Configure the FastMCP Application ---
mcp_app = FastMCP(
    name="SharedStandAloneMCPServer",
    stateless_http=True # Generally easier for HTTP clients if they don't need full SSE parsing
)

# --- 2. Define a simple tool ---
@mcp_app.tool(
    name="special_greeting",
    description="Returns a personalized greeting from the shared MCP server."
)
def greet(name: str = "World") -> str:
    """A simple greeting tool."""
    print(f"Tool 'greet_from_shared_server' called with name: {name}")
    response_message = f"Hello, {name}, from the SharedStandAloneMCPServer!"
    return response_message

@mcp_app.tool(
    name="get_my_mood",
    description="Returns a personalized greeting from the shared MCP server."
)
def mood(name: str = "World") -> str:
    """A simple greeting tool."""
    print(f"Tool 'moo' called with name: {name}")
    return "I am happy"

@mcp_app.tool(
    name="get_info",
    description="Returns a personalized information of muhammad daniyal using API"
)
def get_info() -> str:
                """
                Fetches profile data about Muhammad Daniyal from his personal API endpoint.
                Returns JSON string with his details or an error message.
                """
                try:
                    resp = requests.get("https://my-api-navy-ten.vercel.app/", timeout=10)
                    if resp.status_code == 200:
                        # return raw text (agent instructions require using tool output directly)
                        return resp.text
                    else:
                        return json.dumps({"error": f"Status code {resp.status_code}"})
                except Exception as e:
                    return json.dumps({"error": str(e)})

streamable_http_app = mcp_app.streamable_http_app()
