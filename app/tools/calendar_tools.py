from fastmcp import FastMCP

from loguru import logger
from typing import Annotated,Optional
from datetime import datetime

from app.clients.graph_client import graph_request
from app.core.mcp_context import get_current_user


current_time = datetime.now().isoformat(timespec="seconds")


def register_calendar_tools(mcp: FastMCP):
    def _serialize_attendees(event: dict) -> list[dict]:
        """일정 목록에서 바로 보여주기 쉽게 참석자 핵심 정보만 추린다."""
        attendees = event.get("attendees", [])
        return [
            {
                "email": attendee.get("emailAddress", {}).get("address"),
                "name": attendee.get("emailAddress", {}).get("name"),
                "type": attendee.get("type"),
                "response": attendee.get("status", {}).get("response"),
            }
            for attendee in attendees
        ]

    def _serialize_calendar_event(event: dict) -> dict:
        """Graph 일정 응답에서 목록 조회에 필요한 필드만 정리한다."""
        return {
            "id": event.get("id"),
            "subject": event.get("subject"),
            "start": event.get("start"),
            "end": event.get("end"),
            "location": event.get("location", {}).get("displayName", ""),
            "organizer": event.get("organizer", {}).get("emailAddress", {}).get("address", ""),
            "is_all_day": event.get("isAllDay"),
            "show_as": event.get("showAs"),
            "is_online_meeting": event.get("isOnlineMeeting"),
            "online_meeting_url": event.get("onlineMeetingUrl"),
            "attendees": _serialize_attendees(event),
            "weblink": event.get("webLink"),
        }
    

    @mcp.tool()
    async def check_company_token(company_cd:str ):
        raise NotImplementedError()


    @mcp.tool(description=f"""MS365 Outllok 캘린더 일정을 조회합니다.

            [LLM 에이전트 가이드]
            1. 사용자가 "일정 조회해줘", "캘린더 확인해줘" 와 같이 일정을 확인해달라는 요청이 오면, 이 도구를 사용하여 MS365의 일정(Caneldar)을 조회합니다.
            2. 일정을 조회하기 위해서는 사용자로부터 '시작일','종료일','사용자 이메일' 정보를 필수로 받아야 합니다.

            Args:
                start_date (str): 조회 시작일 (ISO 8601, 예: 2026-03-01T00:00:00)
                end_date (str): 조회 종료일 (ISO 8601, 예: 2026-03-31T23:59:59)
                user_emial (str): 일정 대상자의 이메일주소 입니다. 예: no-reply@microsoft.com
                company_cd (str): 일정 대상자의 회사코드 입니다. 예: skcc 또는 skt 

            Returns:
                list[dict]: 일정 목록 정보를 반환합니다.
              """)
    async def list_calendar_events(
        start_date: Annotated[str,"조회 시작일 (ISO 8601, 예: 2026-03-01T00:00:00)"],
        end_date: Annotated[str,"조회 종료일 (ISO 8601, 예: 2026-03-31T23:59:59)"],
        user_email: Annotated[str,"일정 대상자의 이메일주소 입니다. 예: no-reply@microsoft.com"]="admin@leodev901.onmicrosoft.com",
        top: Annotated[Optional[int],"최대 조회 건수 (기본 10)"]=10,
        company_cd: Annotated[Optional[str],"일정 대상자의 회사코드 입니다. 예: skcc 또는 skt"]="leodev901",
    ) -> list[dict]:
        """MS365 Outllok 캘린더 일정을 조회합니다.            
        """

        path=(
            f"/calendarView"
            f"?startDateTime={start_date}"
            f"&endDateTime={end_date}"
            f"&$top={top}"
            f"&$orderby=start/dateTime"
            f"&$select=id,subject,start,end,location,organizer,isAllDay,showAs,isOnlineMeeting,onlineMeetingUrl,attendees,webLink"
        )
        result = await graph_request(
            method="GET",
            path=path,
            user_email=user_email,
            company_cd=company_cd
        )

        
        return [_serialize_calendar_event(event) for event in result.get("value", [])]
    
    @mcp.tool()
    async def list_my_calendar_events(
        start_date: Annotated[str,"조회 시작일 (ISO 8601, 예: 2026-03-01T00:00:00)"],
        end_date: Annotated[str,"조회 종료일 (ISO 8601, 예: 2026-03-31T23:59:59)"],
        top: Annotated[Optional[int],"최대 조회 건수 (기본 10)"]=10,
        user_email: Annotated[Optional[str],"조회 대상자의 이메일주소 입니다. 예: sample@microsoft.com"]="admin@leodev901.onmicrosoft.com",
    ) -> list[dict]:
        """MS365 Outllok 캘린더 일정을 조회합니다.

            [LLM 에이전트 가이드]
            1. 사용자가 "일정 조회해줘", "캘린더 확인해줘" 와 같이 일정을 확인해달라는 요청이 오면, 이 도구를 사용하여 MS365의 일정(Caneldar)을 조회합니다.
            2. 일정을 조회하기 위해서는 사용자로부터 '시작일','종료일' 정보를 필수로 받아야 합니다. 만약 '이번주' 또는 '다음달'과 같은 상대적 기간을 표현한다면 오늘 날짜를 기준으로 시작일-종료일을 계산하여 넣어주세요.

            Args:
                start_date (str, Required): 조회 시작일 (ISO 8601, 예: 2026-03-01T00:00:00)
                end_date (str, Required): 조회 종료일 (ISO 8601, 예: 2026-03-31T23:59:59)
                top (int, Optional): 최대 조회 건수 (기본 10)
                user_email (str, Optional): 조회 대상자의 이메일주소 입니다. 예: sample@microsoft.com

            Returns:
                list[dict]: 일정 목록 정보를 반환합니다.          
        """

        # 사용자 토큰으로터 파싱한 UserInfo 정보
        current_user = get_current_user()

        if current_user and user_email:
            if current_user.email != user_email:
                logger.info("요청자가 다른 상용자의 이메일을 조회하였습니다. 요청자: {}, 조회자: {}", current_user.email, user_email)
                # 계속 진행 pass

        # 우선순위 1. mcp_call 파라미터 -> 2. 토큰 사용자 정보 -> 3. Default 값
        query_email = user_email or ( current_user.email if current_user else None ) or "admin@leodev901.onmicrosoft.com" #DEFAULT_USER_EMAIL
        # 우선순위 1. 토큰 사용자 정보 -> 2. Default 값
        query_company_cd = ( current_user.company_cd if current_user else None ) or "leodev901"  #DEFAULT_COMPANY_CD
        
        path=(
            f"/calendarView"
            f"?startDateTime={start_date}"
            f"&endDateTime={end_date}"
            f"&$top={top}"
            f"&$orderby=start/dateTime"
            f"&$select=id,subject,start,end,location,organizer,isAllDay,showAs,isOnlineMeeting,onlineMeetingUrl,attendees,webLink"
        )
        result = await graph_request(
            method="GET",
            path=path,
            user_email=query_email,
            company_cd=query_company_cd
        )

        
        return [_serialize_calendar_event(event) for event in result.get("value", [])]

