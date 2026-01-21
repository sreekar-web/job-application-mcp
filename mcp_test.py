from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Test MCP")

@mcp.tool()
def ping():
    """Simple connectivity test"""
    return "MCP connection is working"

if __name__ == "__main__":
    mcp.run()
