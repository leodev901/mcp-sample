from fastmcp import FastMCP

from app.core.http_middleware import HttpMiddleware
from app.core.http_asgi_middleware import HttpLoggingASGIMiddleware
from app.core.mcp_midleware import MCPLoggingMiddleware
from app.tools.calendar_tools import register_calendar_tools


def create_app():
    mcp = FastMCP(
        "MS365 FastMCP Server",
        instructions="MS365 Outlook mail/calendar/todo/teams tools",
    )

    register_calendar_tools(mcp)
    mcp.add_middleware(MCPLoggingMiddleware())

    app = mcp.http_app(path="/mcp", transport="streamable-http")
    
    app.add_middleware(HttpLoggingASGIMiddleware)
    app.add_middleware(HttpMiddleware)

    return app

app = create_app()


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=8002, lifespan="on")
