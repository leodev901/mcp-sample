from typing import Optional

from pydantic import TypeAdapter

from app.clients.graph_client import graph_request
from app.schemas.calendar import CalendarEventDetail, CalendarView


class CalendarService:
    async def list_calendar_view(
        self,
        start_date: str,
        end_date: str,
        top: int | None,
        user_email: str,
        company_cd: str,
    ) -> list[CalendarView]:
        # $top은 Graph API에서 최대 반환 개수를 뜻하므로 None 또는 잘못된 값이면 기본값 10을 사용합니다.
        query_top = top if top is not None and top > 0 else 10

        path = (
            f"/calendarView"
            f"?startDateTime={start_date}"
            f"&endDateTime={end_date}"
            f"&$top={query_top}"
            f"&$orderby=start/dateTime"
            f"&$select=id,subject,start,end,location,organizer,isAllDay,showAs,"
            f"isOnlineMeeting,onlineMeetingUrl,attendees,webLink,bodyPreview"
        )
        result = await graph_request(method="GET", path=path, user_email=user_email, company_cd=company_cd)

        # Graph 목록 응답은 value 키에 배열이 들어오므로 배열만 모델로 검증합니다.
        return TypeAdapter(list[CalendarView]).validate_python(result.get("value", []))

    async def get_calendar_event(self, event_id: str, user_email: str, company_cd: str) -> CalendarEventDetail:
        # 상세 조회는 본문과 중요도까지 포함되므로 별도 상세 스키마로 검증합니다.
        result = await graph_request(method="GET", path=f"/events/{event_id}", user_email=user_email, company_cd=company_cd)
        return CalendarEventDetail.model_validate(result)

    async def create_calendar_event(
        self,
        subject: str,
        start_date: str,
        end_date: str,
        user_email: str,
        company_cd: str,
        body: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
        is_online_meeting: bool = False,
    ) -> CalendarEventDetail:
        # Graph 일정 생성 payload는 start/end를 dateTime/timeZone 객체로 보내야 합니다.
        payload: dict = {
            "subject": subject,
            "start": {"dateTime": start_date, "timeZone": "Asia/Seoul"},
            "end": {"dateTime": end_date, "timeZone": "Asia/Seoul"},
        }
        if body:
            payload["body"] = {"contentType": "HTML", "content": body}
        if location:
            payload["location"] = {"displayName": location}
        if attendees:
            payload["attendees"] = [
                {"emailAddress": {"address": email.strip()}, "type": "required"}
                for email in attendees
                if email and email.strip()
            ]
        if is_online_meeting:
            payload["isOnlineMeeting"] = True
            payload["onlineMeetingProvider"] = "teamsForBusiness"

        result = await graph_request(
            method="POST",
            path="/events",
            json_body=payload,
            user_email=user_email,
            company_cd=company_cd,
        )
        return CalendarEventDetail.model_validate(result)

    async def update_calendar_event(
        self,
        event_id: str,
        user_email: str,
        company_cd: str,
        subject: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        body: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
        is_online_meeting: Optional[bool] = None,
    ) -> CalendarEventDetail:
        # None이 아닌 필드만 PATCH payload에 담아 부분 수정 동작을 명확하게 유지합니다.
        payload: dict = {}
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
                for email in attendees
                if email and email.strip()
            ]
        if is_online_meeting is not None:
            payload["isOnlineMeeting"] = is_online_meeting
            if is_online_meeting:
                payload["onlineMeetingProvider"] = "teamsForBusiness"

        if not payload:
            raise ValueError("수정할 일정 항목이 하나 이상 필요합니다.")

        result = await graph_request(
            method="PATCH",
            path=f"/events/{event_id}",
            json_body=payload,
            user_email=user_email,
            company_cd=company_cd,
        )
        return CalendarEventDetail.model_validate(result)

    async def delete_calendar_event(self, event_id: str, user_email: str, company_cd: str) -> dict:
        # Graph DELETE는 204를 반환하므로 도구 응답으로 사용할 성공 메시지를 직접 구성합니다.
        await graph_request(method="DELETE", path=f"/events/{event_id}", user_email=user_email, company_cd=company_cd)
        return {"status": "success", "event_id": event_id, "message": "일정을 삭제했습니다."}

    async def search_user_by_name(self, search_name: str, user_email: str, company_cd: str) -> list[dict]:
        # displayName 완전 일치 검색으로 사람 이름을 이메일 주소로 변환하는 보조 도구입니다.
        path = f"/users?$filter=displayName eq '{search_name}'"
        result = await graph_request(
            method="GET",
            path=path,
            user_email=user_email,
            company_cd=company_cd,
            is_replace_path=True,
        )
        users = result.get("value", [])
        if not users:
            return [{"message": "검색 결과가 없습니다."}]
        return [{"name": user.get("displayName"), "email": user.get("mail") or user.get("userPrincipalName")} for user in users]
