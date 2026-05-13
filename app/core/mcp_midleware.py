import asyncio
import time
from typing import Any
from datetime import datetime

from fastmcp.server.middleware.middleware import CallNext, Middleware, MiddlewareContext
from loguru import logger
from mcp.types import CallToolRequestParams
from fastmcp.server.dependencies import get_http_request
from app.security.jwt_auth import get_user_from_token
from app.clients.mcp_client import save_mcp_tool_logs
import json

from app.models.logging import MCPToolLogRequest




def logging_message( record: MCPToolLogRequest)->None:
    message=f"[mcp_tool_call] >>> trace_id={record.trace_id}"
    message+=f" status={record.status} "
    message+=f"tool_name={record.tool_name} "
    message+=f"arguments={record.arguments} "
    message+=f"elapsed_ms={record.elapsed_ms} "
    message+=f"user_id={record.user_id} "
    message+=f"email={record.email} "
    message+=f"company_cd={record.company_cd} "

    if record.input is not None:
        message+=f"input={record.input} "
    if record.output is not None:
        message+=f"output={record.output} "
    if record.error_message is not None:
        message+=f"error_message={record.error_message} "
    
    if(record.status=="error"):
        logger.exception(message)
    else:
        logger.info(message)


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
        data = {
            "name": tool_name,
            "arguments": arguments,
        }
        input_json = json.dumps(data, ensure_ascii=False, indent=2)


        # 사용자 JWT_Token에서 사용자 정보 파싱하여 저장

        request = get_http_request()
        trace_id = getattr(request.state, "trace_id", "-")
        user_token = getattr(request.state, "user_token", None)
        current_user = getattr(request.state, "current_user", None)

        if current_user is None and user_token:
            current_user = await get_user_from_token(user_token)
            if current_user:
                request.state.current_user = current_user
                logger.debug(f"get user_info from token success!!! current_user={current_user}")
        

        started = time.perf_counter()

        record = MCPToolLogRequest(
                trace_id=trace_id,
                tool_name=tool_name,
                arguments=arguments,
                # Pydantic 모델의 필수 필드는 생성 시점에 기본 상태를 명시해 둡니다.
                elapsed_ms=0.0,
                status="pending",
                requested_at=datetime.now(),
                user_id=current_user.user_id if current_user else None,
                email=current_user.email if current_user else None,
                company_cd=current_user.company_cd if current_user else None,
                input=input_json,
            )
        try:
            result = await call_next(context)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            
            content_json = json.dumps(
                        result.structured_content,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                        ) if result.structured_content else None
            
            record.status = "success"
            record.output = content_json
            record.responded_at = datetime.now()
            record.elapsed_ms = elapsed_ms
            
            
            return result
        except Exception as e: 
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            
            record.status = "error"
            record.responded_at = datetime.now()
            record.elapsed_ms = elapsed_ms
            record.error_message = f"{type(e).__name__}: {e}"
            
            raise
        finally:

            logging_message(record)
            # save_mcp_tool_logs는 비동기 함수 별도 TASK로 실행
            asyncio.create_task(save_mcp_tool_logs(record))


