from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
mcp = FastMCP(name="Hello Prompt",stateless_http=True)


@mcp.prompt()
def hello_prompts() -> list[base.UserMessage]:
    user_message = f"Hello"
    return [base.UserMessage(content = user_message),base.AssistantMessage(content="Hello ! nie to meet you.")]

mcp_server = mcp.streamable_http_app()
