from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Annotated, Literal, Optional


ShowAsStatus = Literal["free", "busy", "tentative", "oof", "working", "away", "unknown"]
ImportanceStatus = Literal["low", "normal", "high"]


class GraphBaseModel(BaseModel):
    # MS Graph는 camelCase 키를 사용하므로 Python의 snake_case 필드와 자동 매핑합니다.
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class EmailAddressInfo(GraphBaseModel):
    name: Annotated[Optional[str], Field(None, description="이름")]
    address: Annotated[Optional[str], Field(None, description="이메일 주소")]


class EmailAddress(GraphBaseModel):
    # Graph 응답의 emailAddress 객체를 email_address 필드로 받습니다.
    email_address: Annotated[Optional[EmailAddressInfo], Field(None, description="이메일 주소 정보")]


class DateTimeTimeZone(GraphBaseModel):
    # Graph Calendar의 start/end는 문자열이 아니라 dateTime/timeZone 객체입니다.
    date_time: Annotated[Optional[str], Field(None, description="일정 일시")]
    time_zone: Annotated[Optional[str], Field(None, description="시간대")]


class LocationInfo(GraphBaseModel):
    # location은 displayName 등을 가진 객체이므로 문자열 대신 모델로 받습니다.
    display_name: Annotated[Optional[str], Field(None, description="장소 이름")]


class CalendarView(GraphBaseModel):
    id: Annotated[Optional[str], Field(None, description="일정 고유 ID")]
    subject: Annotated[Optional[str], Field(None, description="일정 제목")]

    start: Annotated[Optional[DateTimeTimeZone], Field(None, description="일정 시작 일시")]
    end: Annotated[Optional[DateTimeTimeZone], Field(None, description="일정 종료 일시")]

    location: Annotated[Optional[LocationInfo], Field(None, description="일정 장소")]
    organizer: Annotated[Optional[EmailAddress], Field(None, description="일정 주최자")]
    attendees: Annotated[Optional[list[EmailAddress]], Field(None, description="일정 참석자 목록")]

    is_all_day: Annotated[Optional[bool], Field(None, description="종일 일정 여부")]
    is_online_meeting: Annotated[Optional[bool], Field(None, description="온라인 회의 여부")]
    online_meeting_url: Annotated[Optional[str], Field(None, description="온라인 회의 URL")]
    show_as: Annotated[Optional[ShowAsStatus], Field(None, description="일정 표시 방식")]
    web_link: Annotated[Optional[str], Field(None, description="일정 웹 링크")]
    body_preview: Annotated[Optional[str], Field(None, description="일정 본문 미리보기")]


class BodyInfo(GraphBaseModel):
    content_type: Annotated[Optional[str], Field(None, description="본문 타입")]
    content: Annotated[Optional[str], Field(None, description="본문 내용")]


class CalendarEventDetail(CalendarView):
    body: Annotated[Optional[BodyInfo], Field(None, description="일정 상세 내용")]
    importance: Annotated[Optional[ImportanceStatus], Field(None, description="중요도")]
    categories: Annotated[Optional[list[str]], Field(None, description="일정 범주 목록")]
    is_cancelled: Annotated[Optional[bool], Field(None, description="취소 여부")]
