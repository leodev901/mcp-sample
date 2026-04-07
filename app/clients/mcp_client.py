# app/clients/mcp_client.py
# async def 는 await 로 호출되는 비동기 함수를 뜻합니다.
# 반환값이 본 요청에 필요 없으므로 None 으로 두는 편이 설계가 명확합니다.

import httpx
from loguru import logger

from app.clients.http_client import get_httpx_client
from app.models.logging import MCPToolLogRequest




async def save_mcp_tool_logs(record: MCPToolLogRequest) -> None:
    # 공통 API 로깅 실패가 MCP 응답을 깨면 안 되므로 내부에서 예외를 삼킵니다.
    try:
        payload = record.model_dump(mode="json")

        client = await get_httpx_client()
        response = await client.post(
            "http://localhost:8003/api/logs/tools",
            json=payload,  # json= 은 Python dict 를 JSON 본문으로 보내는 문법입니다.
            headers={"Content-Type": "application/json"},
            timeout=3.0,
        )
        response.raise_for_status()
    except Exception:
        logger.exception("failed to save mcp tool log")
