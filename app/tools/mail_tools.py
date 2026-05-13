from typing import Annotated, Optional

from fastmcp import FastMCP

from app.common.graph_error_wrapper import graph_error_wrapper
from app.schemas.mail import MailDetail, MailSummary
from app.services.mail_service import MailService
from app.tools.tool_context import get_request_current_user, resolve_graph_user


def register_mail_tools(mcp: FastMCP):
    mail_service = MailService()

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def mail_recent_list(
        top: Annotated[Optional[int], "최대 조회할 최근 메일 수입니다. 기본값은 10입니다."] = 10,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[MailSummary]:
        """받은 편지함의 최근 메일 목록을 조회합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 최근 메일, 받은 메일, 새 메일 목록을 요청하면 사용합니다.
        2. 반환된 id는 mail_detail에서 상세 조회에 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await mail_service.get_recent_emails(top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def mail_unread_list(
        top: Annotated[Optional[int], "최대 조회할 읽지 않은 메일 수입니다. 기본값은 10입니다."] = 10,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[MailSummary]:
        """읽지 않은 메일 목록을 조회합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 안 읽은 메일이나 미확인 메일을 요청하면 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await mail_service.get_unread_emails(top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def mail_important_or_flagged_list(
        top: Annotated[Optional[int], "최대 조회할 중요 또는 플래그 메일 수입니다. 기본값은 10입니다."] = 10,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[MailSummary]:
        """중요 메일 또는 플래그 표시된 메일을 조회합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 급한 메일, 중요 메일, 표시해 둔 메일을 요청하면 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await mail_service.get_important_or_flagged_emails(top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def mail_search_by_keyword(
        keyword: Annotated[str, "검색할 메일 키워드입니다. 제목 또는 본문 검색에 사용합니다."],
        top: Annotated[Optional[int], "최대 조회 건수입니다. 기본값은 10입니다."] = 10,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[MailSummary]:
        """메일 제목 또는 본문에서 키워드를 검색합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 특정 주제, 프로젝트명, 문구가 들어간 메일을 찾을 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await mail_service.search_emails_by_keyword(keyword, top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def mail_search_by_sender(
        sender: Annotated[str, "검색할 발신자 이름 또는 이메일 일부입니다."],
        top: Annotated[Optional[int], "최대 조회 건수입니다. 기본값은 10입니다."] = 10,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[MailSummary]:
        """발신자 이름 또는 이메일 주소 기준으로 메일을 검색합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 특정 사람이 보낸 메일을 요청하면 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await mail_service.search_emails_by_sender(sender, top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def mail_search_by_attachment(
        top: Annotated[Optional[int], "최대 조회 건수입니다. 기본값은 10입니다."] = 10,
        file_name_keyword: Annotated[Optional[str], "첨부파일 이름에 포함될 키워드입니다. 비우면 첨부파일이 있는 메일만 조회합니다."] = None,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[MailSummary]:
        """첨부파일이 있는 메일을 조회하고 선택적으로 파일명 키워드로 좁힙니다.

        [LLM 에이전트 가이드]
        1. 사용자가 첨부파일이 있는 메일이나 특정 파일명을 포함한 메일을 찾을 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await mail_service.search_emails_by_attachment(top, query_email, query_company_cd, file_name_keyword)

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def mail_sent_list(
        top: Annotated[Optional[int], "최대 조회할 보낸 메일 수입니다. 기본값은 10입니다."] = 10,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[MailSummary]:
        """보낸 편지함의 최근 메일 목록을 조회합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 자신이 보낸 메일이나 발송 내역을 확인하려 할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await mail_service.get_sent_emails(top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=False)
    async def mail_detail(
        message_id: Annotated[str, "상세 조회할 메일 ID입니다. 메일 목록 도구 반환값의 id를 사용합니다."],
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> MailDetail:
        """단일 메일의 상세 본문과 첨부파일 목록을 조회합니다.

        [LLM 에이전트 가이드]
        1. 목록에서 특정 메일의 전체 내용이나 첨부파일 이름이 필요할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await mail_service.get_email_detail(message_id, query_email, query_company_cd)
