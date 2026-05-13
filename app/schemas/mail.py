from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class MailBaseModel(BaseModel):
    # Graph 메일 응답과 도구 반환값 모두를 받을 수 있도록 alias를 허용합니다.
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class MailAddress(MailBaseModel):
    name: Annotated[Optional[str], Field(None, description="이름")]
    address: Annotated[Optional[str], Field(None, description="이메일 주소")]


class MailSummary(MailBaseModel):
    id: Annotated[Optional[str], Field(None, description="메일 ID")]
    subject: Annotated[Optional[str], Field(None, description="메일 제목")]
    sender: Annotated[Optional[MailAddress], Field(None, description="발신자")]
    received_date_time: Annotated[Optional[str], Field(None, description="수신 일시")]
    sent_date_time: Annotated[Optional[str], Field(None, description="발신 일시")]
    body_preview: Annotated[Optional[str], Field(None, description="본문 미리보기")]
    importance: Annotated[Optional[str], Field(None, description="중요도")]
    is_read: Annotated[Optional[bool], Field(None, description="읽음 여부")]
    has_attachments: Annotated[Optional[bool], Field(None, description="첨부파일 여부")]
    web_link: Annotated[Optional[str], Field(None, description="Outlook 웹 링크")]


class MailAttachment(MailBaseModel):
    id: Annotated[Optional[str], Field(None, description="첨부파일 ID")]
    name: Annotated[Optional[str], Field(None, description="첨부파일 이름")]
    content_type: Annotated[Optional[str], Field(None, description="콘텐츠 타입")]
    size: Annotated[Optional[int], Field(None, description="파일 크기")]


class MailDetail(MailSummary):
    body: Annotated[Optional[dict], Field(None, description="메일 본문")]
    attachments: Annotated[Optional[list[MailAttachment]], Field(None, description="첨부파일 목록")]
