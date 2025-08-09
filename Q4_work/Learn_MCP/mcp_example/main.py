from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="MCP CLIENT", stateless_http = True)

@mcp.tool()
def hello(name:str):
    return f"Hello {name}!"


mcp_server = mcp.streamable_http_app()
