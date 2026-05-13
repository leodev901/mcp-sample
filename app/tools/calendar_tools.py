from datetime import datetime
from typing import Annotated, Optional

from fastmcp import FastMCP

from app.common.graph_error_wrapper import graph_error_wrapper
from app.schemas.calendar import CalendarEventDetail, CalendarView
from app.services.calendar_service import CalendarService
from app.tools.tool_context import get_request_current_user, resolve_graph_user


def register_calendar_tools(mcp: FastMCP):
    calendar_service = CalendarService()

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def calendar_list(
        start_date: Annotated[str, "조회 시작일입니다. ISO 8601 형식으로 입력합니다. 예: 2026-03-01T00:00:00"] = "2026-03-01T00:00:00",
        end_date: Annotated[str, "조회 종료일입니다. ISO 8601 형식으로 입력합니다. 예: 2026-03-31T23:59:59"] = "2026-03-31T23:59:59",
        top: Annotated[Optional[int], "최대 조회 건수입니다. 기본값은 10입니다."] = 10,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[CalendarView]:
        """MS365 Outlook 캘린더 일정을 조회합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 일정 조회, 캘린더 확인, 이번 주 일정 확인을 요청하면 이 도구를 사용합니다.
        2. 상대 기간 표현은 오늘 날짜를 기준으로 ISO 8601 시작/종료일로 계산해서 전달합니다.
        3. 반환된 id는 calendar_detail, calendar_update, calendar_delete에서 다시 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)

        return await calendar_service.list_calendar_view(
            start_date=start_date,
            end_date=end_date,
            top=top,
            user_email=query_email,
            company_cd=query_company_cd,
        )

    @mcp.tool()
    @graph_error_wrapper(as_list=False)
    async def calendar_detail(
        event_id: Annotated[str, "조회할 일정의 고유 ID입니다. calendar_list 반환값의 id를 사용합니다."],
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> CalendarEventDetail:
        """단일 캘린더 일정의 상세 정보를 조회합니다.

        [LLM 에이전트 가이드]
        1. 목록 조회 후 특정 일정의 본문, 참석자, 중요도 등 구체 내용이 필요할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await calendar_service.get_calendar_event(event_id, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=False)
    async def calendar_create(
        subject: Annotated[str, "일정 제목입니다."],
        start_date: Annotated[str, "일정 시작 일시입니다. ISO 8601 형식, 한국 시간 기준입니다. 예: 2026-03-01T10:00:00"],
        end_date: Annotated[str, "일정 종료 일시입니다. ISO 8601 형식, 한국 시간 기준입니다. 예: 2026-03-01T11:00:00"],
        user_email: Annotated[Optional[str], "일정을 생성할 사용자 이메일 주소입니다. 예: user@example.com"] = None,
        body: Annotated[Optional[str], "일정 상세 내용입니다. HTML 또는 일반 텍스트를 입력합니다."] = None,
        location: Annotated[Optional[str], "일정 장소 이름입니다."] = None,
        attendees: Annotated[Optional[list[str]], "참석자 이메일 주소 목록입니다. 예: ['a@example.com', 'b@example.com']"] = None,
        is_online_meeting: Annotated[Optional[bool], "Teams 온라인 회의 생성 여부입니다."] = False,
    ) -> CalendarEventDetail:
        """새로운 캘린더 일정을 생성합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 회의나 약속을 새로 잡아달라고 요청할 때 사용합니다.
        2. start_date와 end_date는 한국 시간 기준 ISO 8601 문자열로 전달합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await calendar_service.create_calendar_event(
            subject=subject,
            start_date=start_date,
            end_date=end_date,
            user_email=query_email,
            company_cd=query_company_cd,
            body=body,
            location=location,
            attendees=attendees,
            is_online_meeting=bool(is_online_meeting),
        )

    @mcp.tool()
    @graph_error_wrapper(as_list=False)
    async def calendar_update(
        event_id: Annotated[str, "수정할 일정의 고유 ID입니다. calendar_list 반환값의 id를 사용합니다."],
        user_email: Annotated[Optional[str], "수정 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
        subject: Annotated[Optional[str], "변경할 일정 제목입니다."] = None,
        start_date: Annotated[Optional[str], "변경할 시작 일시입니다. ISO 8601 형식, 한국 시간 기준입니다."] = None,
        end_date: Annotated[Optional[str], "변경할 종료 일시입니다. ISO 8601 형식, 한국 시간 기준입니다."] = None,
        body: Annotated[Optional[str], "변경할 상세 내용입니다."] = None,
        location: Annotated[Optional[str], "변경할 장소 이름입니다."] = None,
        attendees: Annotated[Optional[list[str]], "변경할 참석자 이메일 목록입니다."] = None,
        is_online_meeting: Annotated[Optional[bool], "온라인 회의 설정 여부입니다."] = None,
    ) -> CalendarEventDetail:
        """기존 캘린더 일정을 부분 수정합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 기존 일정의 제목, 시간, 장소, 참석자 등을 바꿔달라고 할 때 사용합니다.
        2. 변경할 값만 채우고 나머지는 None으로 둡니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await calendar_service.update_calendar_event(
            event_id=event_id,
            user_email=query_email,
            company_cd=query_company_cd,
            subject=subject,
            start_date=start_date,
            end_date=end_date,
            body=body,
            location=location,
            attendees=attendees,
            is_online_meeting=is_online_meeting,
        )

    @mcp.tool()
    @graph_error_wrapper(as_list=False)
    async def calendar_delete(
        event_id: Annotated[str, "삭제할 일정의 고유 ID입니다. calendar_list 반환값의 id를 사용합니다."],
        user_email: Annotated[Optional[str], "삭제 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> dict:
        """기존 캘린더 일정을 삭제합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 특정 일정을 취소하거나 삭제해달라고 할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await calendar_service.delete_calendar_event(event_id, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def search_email_by_name(
        search_name: Annotated[str, "검색할 사용자 이름입니다. 예: 홍길동"],
    ) -> list[dict]:
        """M365 사용자 이름으로 이메일 주소를 검색합니다.

        [LLM 에이전트 가이드]
        1. 다른 도구 호출에 이메일이 필요한데 사용자가 이름만 말한 경우 먼저 사용합니다.
        2. 검색 결과가 여러 명이면 사용자에게 정확한 이메일 주소를 다시 확인합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(None, current_user)
        return await calendar_service.search_user_by_name(search_name, query_email, query_company_cd)
