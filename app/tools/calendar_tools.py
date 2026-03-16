from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request

from loguru import logger
from typing import Annotated,Optional
from datetime import datetime

from app.clients.graph_client import graph_request
from app.models.user_info import UserInfo


current_time = datetime.now().isoformat(timespec="seconds")

BLACKLIST = [
    "admin@skcc.com",
]


def register_calendar_tools(mcp: FastMCP):

    def _is_black_list(email: str) -> bool:
        return email in BLACKLIST

    def _get_request_current_user() -> UserInfo | None:
        # Tool 이 HTTP 요청 바깥에서도 호출될 수 있어, 요청이 없으면 None 으로 둔다.
        try:
            request = get_http_request()
        except RuntimeError:
            logger.error(f"현재 사용자 정보를 가져오는 중 오류 발생: {str(e)}")
            return None

        return getattr(request.state, "current_user", None)

    def _get_request_trace_id() -> str | None:
        # Tool 이 HTTP 요청 바깥에서도 호출될 수 있어, 요청이 없으면 None 으로 둔다.
        try:
            request = get_http_request()
        except RuntimeError:
            logger.error(f"현재 사용자 정보를 가져오는 중 오류 발생: {str(e)}")
            return None

        return getattr(request.state, "trace_id", None)    

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
    
    def _serialize_calendar_event_detail(event: dict) -> dict:
        """Graph 일정 응답에서 단일 상세 조회 시 필요한 전체 필드를 정리한다."""
        base_event = _serialize_calendar_event(event)
        
        # 상세 정보 추가
        base_event.update({
            "body_content": event.get("body", {}).get("content", ""),
            "body_preview": event.get("bodyPreview", ""),
            "importance": event.get("importance", ""),
            "response_status": event.get("responseStatus", {}).get("response", ""),
            "created_time": event.get("createdDateTime", ""),
            "last_modified_time": event.get("lastModifiedDateTime", ""),
            "recurrence": event.get("recurrence"),
        })
        return base_event


    @mcp.tool()
    async def check_company_token(company_cd:str ):
        raise NotImplementedError()


    @mcp.tool()
    async def list_calendar_events(
        start_date: Annotated[str,"조회 시작일 (ISO 8601, 예: 2026-03-01T00:00:00)"]="2026-03-01T00:00:00",
        end_date: Annotated[str,"조회 종료일 (ISO 8601, 예: 2026-03-31T23:59:59)"]="2026-03-31T23:59:59",
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

        trace_id = _get_request_trace_id()
        current_user = _get_request_current_user()
        
        logger.info("현재 trace_id: {}", trace_id)
        if not current_user:
            raise ValueError("현재 사용자 정보를 찾을 수 없습니다. 토큰 정보를 확인해주세요.")
        logger.info("현재 사용자 정보를 가져왔습니다. 사용자: {}", current_user)
        logger.info("현재 사용자 이메일: {}", current_user.email)

        
        # 사용자 정보와 요청 이메일이 다른경우
        if current_user and user_email:
            if current_user.email != user_email:
                logger.info("요청자가 다른 사용자의 이메일을 조회하였습니다. 요청자: {}, 조회자: {}", current_user.email, user_email)
                # 계속 진행 pass

        # 우선순위 1. mcp_call 파라미터 -> 2. 토큰 사용자 정보 -> 3. Default 값
        query_email = user_email or ( current_user.email if current_user else None ) or "admin@leodev901.onmicrosoft.com" #DEFAULT_USER_EMAIL
        # 우선순위 1. 토큰 사용자 정보 -> 2. Default 값
        query_company_cd = ( current_user.company_cd if current_user else None ) or "leodev901"  #DEFAULT_COMPANY_CD
        
        if _is_black_list(query_email):
             raise ValueError("해당 사용자는 접근이 허용되지 않습니다.")

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


    @mcp.tool()
    async def get_calendar_event(
        event_id: Annotated[str, "조회할 일정의 고유 ID (필수)"],
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소 (예: sample@microsoft.com)"] = "admin@leodev901.onmicrosoft.com",
    ) -> dict:
        """단일 캘린더 일정의 상세 정보를 조회합니다.
        
        [LLM 에이전트 가이드]
        1. 목록 조회 후 특정 일정의 구체적인 내용을 확인할 때 사용합니다.
        """
        current_user = _get_request_current_user()
        if not current_user:
            raise ValueError("현재 사용자 정보를 찾을 수 없습니다. 토큰 정보를 확인해주세요.")
            
        query_email = user_email or current_user.email or "admin@leodev901.onmicrosoft.com"
        query_company_cd = current_user.company_cd or "leodev901"
        
        if _is_black_list(query_email):
             raise ValueError("해당 사용자는 접근이 허용되지 않습니다.")

        path = f"/events/{event_id}"
        
        try:
            result = await graph_request(
                method="GET",
                path=path,
                user_email=query_email,
                company_cd=query_company_cd
            )
            return _serialize_calendar_event_detail(result)
        except Exception as e:
            raise RuntimeError(f"일정 상세 조회 중 오류 발생: {str(e)}")


    @mcp.tool()
    async def create_calendar_event(
        subject: Annotated[str, "일정 제목 (필수)"],
        start_date: Annotated[str, "일정 시작 일시 (ISO 8601, KST 기준, 예: 2026-03-01T10:00:00)"],
        end_date: Annotated[str, "일정 종료 일시 (ISO 8601, KST 기준, 예: 2026-03-01T11:00:00)"],
        user_email: Annotated[Optional[str], "생성 대상자의 이메일 주소"] = "admin@leodev901.onmicrosoft.com",
        body: Annotated[Optional[str], "일정 상세 내용 (HTML 또는 일반 텍스트)"] = None,
        location: Annotated[Optional[str], "일정 장소 이름"] = None,
        attendees: Annotated[Optional[list[str]], "참석자 이메일 주소 목록 (예: ['user1@com', 'user2@com'])"] = None,
        is_online_meeting: Annotated[Optional[bool], "Teams 온라인 회의 생성 여부"] = False,
    ) -> dict:
        """새로운 캘린더 일정을 생성합니다.
        
        [LLM 에이전트 가이드]
        1. 사용자가 "내일 10시에 회의 일정 잡아줘" 등의 요청 시 사용합니다.
        2. start_date와 end_date는 한국 시간(KST) 기준으로 작성해야 합니다.
        """
        current_user = _get_request_current_user()
        if not current_user:
            raise ValueError("현재 사용자 정보를 찾을 수 없습니다. 토큰 정보를 확인해주세요.")
            
        query_email = user_email or current_user.email or "admin@leodev901.onmicrosoft.com"
        query_company_cd = current_user.company_cd or "leodev901"
        
        if _is_black_list(query_email):
             raise ValueError("해당 사용자는 접근이 허용되지 않습니다.")

        payload = {
            "subject": subject,
            "start": {"dateTime": start_date, "timeZone": "Asia/Seoul"},
            "end": {"dateTime": end_date, "timeZone": "Asia/Seoul"}
        }

        if body:
            payload["body"] = {"contentType": "HTML", "content": body}
        if location:
            payload["location"] = {"displayName": location}
        if attendees:
            payload["attendees"] = [
                {"emailAddress": {"address": email.strip()}, "type": "required"} 
                for email in attendees if email.strip()
            ]
        if is_online_meeting:
            payload["isOnlineMeeting"] = True
            payload["onlineMeetingProvider"] = "teamsForBusiness"

        try:
            result = await graph_request(
                method="POST",
                path="/events",
                json_body=payload,
                user_email=query_email,
                company_cd=query_company_cd
            )
            return _serialize_calendar_event(result)
        except Exception as e:
            raise RuntimeError(f"일정 생성 중 오류 발생: {str(e)}")


    @mcp.tool()
    async def update_calendar_event(
        event_id: Annotated[str, "수정할 일정의 고유 ID (필수)"],
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소"] = "admin@leodev901.onmicrosoft.com",
        subject: Annotated[Optional[str], "변경할 일정 제목"] = None,
        start_date: Annotated[Optional[str], "변경할 시작 일시 (KST)"] = None,
        end_date: Annotated[Optional[str], "변경할 종료 일시 (KST)"] = None,
        body: Annotated[Optional[str], "변경할 상세 내용"] = None,
        location: Annotated[Optional[str], "변경할 장소"] = None,
        attendees: Annotated[Optional[list[str]], "변경할 참석자 이메일 목록"] = None,
        is_online_meeting: Annotated[Optional[bool], "온라인 회의 설정 여부"] = None,
    ) -> dict:
        """기존 캘린더 일정을 수정합니다.
        
        [LLM 에이전트 가이드]
        1. 사용자가 기존 일정의 시간, 장소, 제목 등을 변경해달라고 할 때 사용합니다.
        2. 변경하려는 파라미터만 값을 채워 넣으면 됩니다.
        """
        current_user = _get_request_current_user()
        if not current_user:
            raise ValueError("현재 사용자 정보를 찾을 수 없습니다.")
            
        query_email = user_email or current_user.email or "admin@leodev901.onmicrosoft.com"
        query_company_cd = current_user.company_cd or "leodev901"
        
        if _is_black_list(query_email):
             raise ValueError("해당 사용자는 접근이 허용되지 않습니다.")

        payload = {}
        if subject is not None:
            payload["subject"] = subject
        if start_date is not None:
            payload["start"] = {"dateTime": start_date, "timeZone": "Asia/Seoul"}
        if end_date is not None:
            payload["end"] = {"dateTime": end_date, "timeZone": "Asia/Seoul"}
        if body is not None:
            payload["body"] = {"contentType": "HTML", "content": body}
        if location is not None:
            payload["location"] = {"displayName": location}
        if attendees is not None:
            payload["attendees"] = [
                {"emailAddress": {"address": email.strip()}, "type": "required"} 
                for email in attendees if email.strip()
            ]
        if is_online_meeting is not None:
            payload["isOnlineMeeting"] = is_online_meeting
            if is_online_meeting:
                payload["onlineMeetingProvider"] = "teamsForBusiness"

        if not payload:
            raise ValueError("수정할 항목이 지정되지 않았습니다.")

        try:
            result = await graph_request(
                method="PATCH",
                path=f"/events/{event_id}",
                json_body=payload,
                user_email=query_email,
                company_cd=query_company_cd
            )
            return _serialize_calendar_event(result)
        except Exception as e:
            raise RuntimeError(f"일정 수정 중 오류 발생: {str(e)}")


    @mcp.tool()
    async def delete_calendar_event(
        event_id: Annotated[str, "삭제할 일정의 고유 ID (필수)"],
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소"] = "admin@leodev901.onmicrosoft.com",
    ) -> dict:
        """기존 캘린더 일정을 삭제합니다.
        
        [LLM 에이전트 가이드]
        1. 사용자가 특정 일정을 취소/삭제해달라고 할 때 사용합니다.
        """
        current_user = _get_request_current_user()
        if not current_user:
            raise ValueError("현재 사용자 정보를 찾을 수 없습니다.")
            
        query_email = user_email or current_user.email or "admin@leodev901.onmicrosoft.com"
        query_company_cd = current_user.company_cd or "leodev901"
        
        if _is_black_list(query_email):
             raise ValueError("해당 사용자는 접근이 허용되지 않습니다.")

        try:
            await graph_request(
                method="DELETE",
                path=f"/events/{event_id}",
                user_email=query_email,
                company_cd=query_company_cd
            )
            return {"status": "success", "message": f"일정({event_id})이 성공적으로 삭제되었습니다."}
        except Exception as e:
            raise RuntimeError(f"일정 삭제 중 오류 발생: {str(e)}")

