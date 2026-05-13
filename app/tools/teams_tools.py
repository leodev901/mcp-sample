from typing import Annotated, Optional

from fastmcp import FastMCP

from app.common.graph_error_wrapper import graph_error_wrapper
from app.schemas.teams import TeamsChatMessage, TeamsChatSummary, TeamsSendMessageResult
from app.services.teams_service import TeamsService
from app.tools.tool_context import get_request_current_user, resolve_graph_user


def register_teams_tools(mcp: FastMCP):
    teams_service = TeamsService()

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def teams_list_chats(
        top: Annotated[Optional[int], "최대 조회할 Teams 채팅방 수입니다. 기본값은 10입니다."] = 10,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[TeamsChatSummary]:
        """사용자가 참여 중인 Teams 채팅방 목록을 조회합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 Teams 채팅방 목록이나 최근 대화방을 요청하면 사용합니다.
        2. 반환된 id는 teams_list_chat_messages, teams_send_chat_message에서 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await teams_service.list_chats(top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def teams_list_chat_messages(
        chat_id: Annotated[str, "메시지를 조회할 Teams 채팅방 ID입니다. teams_list_chats 반환값의 id를 사용합니다."],
        top: Annotated[Optional[int], "최대 조회할 최근 메시지 수입니다. 기본값은 15입니다."] = 15,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[TeamsChatMessage]:
        """지정한 Teams 채팅방의 최근 메시지를 조회합니다.

        [LLM 에이전트 가이드]
        1. 특정 채팅방의 최근 대화 내용 확인이 필요할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await teams_service.list_chat_messages(chat_id, top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=False)
    async def teams_send_chat_message(
        chat_id: Annotated[str, "메시지를 보낼 Teams 채팅방 ID입니다."],
        content: Annotated[str, "보낼 메시지 본문입니다. HTML 또는 일반 텍스트를 입력합니다."],
        user_email: Annotated[Optional[str], "메시지를 보낼 사용자 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> TeamsSendMessageResult:
        """Teams 채팅방에 새 메시지를 전송합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 특정 Teams 방에 메시지를 보내달라고 명확히 요청할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await teams_service.send_chat_message(chat_id, content, query_email, query_company_cd)
