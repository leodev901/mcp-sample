from fastmcp import FastMCP

from app.core.config import settings
from app.core.http_middleware import HttpLoggingMiddleware
from app.core.logger_config import setup_logging
from app.core.mcp_midleware import MCPLoggingMiddleware
from app.tools.calendar_tools import register_calendar_tools


def create_app():
    setup_logging(settings.LOG_LEVEL)

    mcp = FastMCP(
        "MS365 FastMCP Server",
        instructions="MS365 Outlook mail/calendar/todo/teams tools",
    )

    register_calendar_tools(mcp)
    mcp.add_middleware(MCPLoggingMiddleware())

    app = mcp.http_app(path="/mcp", transport="streamable-http")
    app.add_middleware(HttpLoggingMiddleware)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002, lifespan="on")
