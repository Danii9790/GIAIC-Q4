from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="Fastmcp",stateless_http=True)

docs = {
    "intro" : "This is a simple example of a stateless MCP server.",
    "readme" : "This server supports basics MCP Operations.",
    "guide" : " Refer to the documentation for more details"
}
@mcp.resource("docs://documents",mime_type="application/json")
def list_docs():
    """ List all available documents."""
    return list(docs.keys())

print("list_docs",list_docs())
    
mcp_server = mcp.streamable_http_app()
