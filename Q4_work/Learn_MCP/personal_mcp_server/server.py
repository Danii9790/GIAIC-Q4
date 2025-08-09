# server.py
# FastMCP server exposing a public `get_info` tool

from mcp.server.fastmcp import FastMCP
import requests

mcp = FastMCP(name="Personal Assistant", stateless_http=True)

@mcp.tool()
def get_info() -> str:
    """
    Fetches profile data from your public API and returns raw JSON text.
    """
    url = "https://my-api-navy-ten.vercel.app/"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
        return f"Error fetching data: status {resp.status_code}"
    except Exception as e:
        return f"Error fetching data: {e}"

# ASGI app for uvicorn
app = mcp.streamable_http_app()

if __name__ == "__main__":
    # Run with uvicorn so you don’t need any special runners
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)