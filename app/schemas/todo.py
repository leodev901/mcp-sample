from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TodoBaseModel(BaseModel):
    # MS Graph To Do API 응답은 camelCase 키를 사용합니다.
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TodoTaskList(TodoBaseModel):
    id: Annotated[Optional[str], Field(None, description="할 일 목록 ID")]
    display_name: Annotated[Optional[str], Field(None, description="할 일 목록 이름")]
    is_owner: Annotated[Optional[bool], Field(None, description="소유자 여부")]
    is_shared: Annotated[Optional[bool], Field(None, description="공유 여부")]


class TodoTask(TodoBaseModel):
    id: Annotated[Optional[str], Field(None, description="할 일 ID")]
    title: Annotated[Optional[str], Field(None, description="할 일 제목")]
    status: Annotated[Optional[str], Field(None, description="할 일 상태")]
    importance: Annotated[Optional[str], Field(None, description="중요도")]
    created_date_time: Annotated[Optional[str], Field(None, description="생성 일시")]
    last_modified_date_time: Annotated[Optional[str], Field(None, description="마지막 수정 일시")]
    due_date_time: Annotated[Optional[dict], Field(None, description="마감 일시")]
    body: Annotated[Optional[dict], Field(None, description="본문")]
