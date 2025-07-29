from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="Hello-mcp", stateless_http = True)

@mcp.tool(name="online_researcher",description="Seach the Web for information")
def seach_online(query:str) ->str :
    return f"Results for {query}...."



mcp_app =mcp.streamable_http_app()
