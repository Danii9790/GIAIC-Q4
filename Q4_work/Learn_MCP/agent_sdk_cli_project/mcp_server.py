from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DoucmentMCP",stateless_http=True)

docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# TODO: Write a tool to read a doc
@mcp.tool()
async def read_docs(docs_id : str) ->str:
    return docs[docs_id]

# TODO: Write a tool to edit a doc
@mcp.tool()
async def edit_docs(docs_id : str,content : str) -> str:
    docs[docs_id] = content
    return "Document edited sucessfully."
# TODO: Write a resource to return all doc id's
# TODO: Write a resource to return the contents of a particular doc
# TODO: Write a prompt to rewrite a doc in markdown format
# TODO: Write a prompt to summarize a doc

mcp_app = mcp.streamable_http_app()