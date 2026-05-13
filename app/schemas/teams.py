from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TeamsBaseModel(BaseModel):
    # MS Graph 응답의 camelCase 키를 Python snake_case 필드에 자동 매핑합니다.
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TeamsChatSummary(TeamsBaseModel):
    id: Annotated[Optional[str], Field(None, description="Teams 채팅방 ID")]
    topic: Annotated[Optional[str], Field(None, description="채팅방 제목")]
    chat_type: Annotated[Optional[str], Field(None, description="채팅방 유형")]
    last_message_preview: Annotated[Optional[str], Field(None, description="마지막 메시지 미리보기")]
    last_updated: Annotated[Optional[str], Field(None, description="마지막 업데이트 일시")]


class TeamsChatMessage(TeamsBaseModel):
    id: Annotated[Optional[str], Field(None, description="메시지 ID")]
    sender: Annotated[Optional[str], Field(None, description="보낸 사람 이름")]
    created_time: Annotated[Optional[str], Field(None, description="메시지 생성 일시")]
    content: Annotated[Optional[str], Field(None, description="메시지 본문")]
    type: Annotated[Optional[str], Field(None, description="메시지 유형")]


class TeamsSendMessageResult(TeamsBaseModel):
    status: Annotated[str, Field(..., description="처리 상태")]
    message_id: Annotated[Optional[str], Field(None, description="생성된 메시지 ID")]
    created_time: Annotated[Optional[str], Field(None, description="생성 일시")]
