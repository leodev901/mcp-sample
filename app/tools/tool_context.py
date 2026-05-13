from typing import Optional

from fastmcp.server.dependencies import get_http_request
from loguru import logger

from app.core.config import settings
from app.models.user_info import UserInfo


def get_request_current_user() -> UserInfo | None:
    # MCP 도구는 HTTP 요청 컨텍스트 밖에서 테스트될 수 있으므로 RuntimeError를 None으로 흡수합니다.
    try:
        request = get_http_request()
    except RuntimeError as e:
        logger.debug(f"HTTP 요청 컨텍스트를 찾을 수 없습니다: {e}")
        return None

    return getattr(request.state, "current_user", None)


def resolve_graph_user(user_email: Optional[str], current_user: UserInfo | None) -> tuple[str, str]:
    # 도구 파라미터를 1순위로 사용하고, 없으면 JWT에서 추출된 사용자 정보를 사용합니다.
    if user_email is not None:
        return user_email, settings.DEFAULT_COMPANY_CD

    if current_user is not None and current_user.email and current_user.company_cd:
        return current_user.email, current_user.company_cd

    # 기본 사용자가 없으면 Graph API를 안전하게 호출할 수 없으므로 명확한 오류를 냅니다.
    if settings.DEFAULT_USER_EMAIL and settings.DEFAULT_COMPANY_CD:
        return settings.DEFAULT_USER_EMAIL, settings.DEFAULT_COMPANY_CD

    raise ValueError("조회 대상 사용자 이메일과 회사 코드가 필요합니다.")
