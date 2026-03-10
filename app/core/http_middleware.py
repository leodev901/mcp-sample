import time
import uuid

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.security.jwt_auth import get_user_from_token

from app.core.mcp_context import (
    clear_trace_id, 
    set_trace_id,
    set_user_token,
    get_user_token,
    clear_user_token,
    set_current_user,
    get_current_user,
    clear_current_user,
)


class HttpLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP 요청으로부터 MCP tool 실행 까지 추적을 위한 trace_id를 만들고 저장한다.
    HTTP 헤더에서 들어온 사용자 인증 JWT 토큰으로 사용자 정보 UserInfo를 컨텍스트 변수에 저장한다. 
    """

    async def dispatch(self, request: Request, call_next):
        # health check는 바로 통과 
        if request.url.path == "/api/health":
            return await call_next(request)

        # 상위 추적 ID를 우선 사용해야 외부 시스템 로그와도 연결된다.
        trace_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        set_trace_id(trace_id)

        started = time.perf_counter()
        status_code = 500

        try:
            # 헤더에서 mcp_user_token을 가져와서 컨텍스트에 저장
            user_token = request.headers.get("mcp_user_token")
            if user_token:
                set_user_token(user_token)

                # user_token에서 사용자 정보를 해석하여 컨텍스트에 저장
                userinfo = await get_user_from_token(user_token)
                if userinfo:
                    set_current_user(userinfo)
                    logger.debug(f"get userinfo from token success!!!! user: {get_current_user()}  trace_id={trace_id}")  
                else:
                    logger.warning(f"no userinfo in trace_id={trace_id}")     
            else:
                logger.warning(f"no mcp_user_token in trace_id={trace_id}")    

            response = await call_next(request)
            status_code = response.status_code
            # 응답에도 같은 값을 돌려줘야 클라이언트와 서버 로그를 쉽게 대조할 수 있다.
            response.headers["x-request-id"] = trace_id
            return response
        
        except Exception:
            logger.exception(
                f"[http_request_failed] >>> trace_id={trace_id}"
                f" method={request.method} path={request.url.path}"
            )
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            client_ip = request.client.host if request.client else "unknown"

            # 지금은 학습과 디버깅이 목적이어서 헤더를 함께 남긴다.
            logger.info(
                f"[http_request] >>> trace_id={trace_id}"
                f" method={request.method} path={request.url.path} status={status_code} elapsed_ms={elapsed_ms:.1f} ip={client_ip}"
                f"\n - headers={dict(request.headers)}"
            )
            clear_trace_id()
            clear_user_token()
            clear_current_user()
