import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger_config import get_logger

logger = get_logger("app.http")


class HttpLoggingMiddleware(BaseHTTPMiddleware):
    """Logs core request/response metadata for HTTP calls."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/api/health":
            return await call_next(request)

        started = time.perf_counter()
        headers = dict(request.headers)
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            logger.exception(
                "http_request_failed method=%s path=%s query=%s",
                request.method,
                request.url.path,
                request.url.query,
            )
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            logger.info(
                "http_request method=%s path=%s status=%s elapsed_ms=%.1f client=%s mcp_session_id=%s",
                request.method,
                request.url.path,
                status_code,
                elapsed_ms,
                request.client.host if request.client else "-",
                headers.get("mcp-session-id", "-"),
            )
