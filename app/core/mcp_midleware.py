import time
from typing import Any

from fastmcp.server.middleware.middleware import CallNext, Middleware, MiddlewareContext
from loguru import logger
from mcp.types import CallToolRequestParams

from app.core.mcp_context import get_trace_id


class MCPLoggingMiddleware(Middleware):
    """
    HTTP 요청에서 저장한 trace_id를 MCP tool 로그에도 붙인다.
    그래서 HTTP 로그 한 줄과 tool 로그 한 줄을 바로 연결해서 볼 수 있다.
    """

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, Any],
    ) -> Any:
        params = context.message
        tool_name = params.name
        arguments = params.arguments or {}
        # argument_keys = list(arguments.keys())
        trace_id = get_trace_id()

        started = time.perf_counter()
        try:
            result = await call_next(context)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            logger.info(
                f"[mcp_tool_call] >>> trace_id={trace_id}"
                f" tool={tool_name} status=success elapsed_ms={elapsed_ms:.1f} arguments={arguments}"
            )
            return result
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            logger.exception(
                f"[mcp_tool_call] >>> trace_id={trace_id}"
                f" tool={tool_name} status=error elapsed_ms={elapsed_ms:.1f} arguments={arguments}"
            )
            raise
