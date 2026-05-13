from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SharePointBaseModel(BaseModel):
    # 도구 반환값은 snake_case를 쓰고 Graph 원본은 camelCase를 쓰므로 둘 다 허용합니다.
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DriveItemSummary(SharePointBaseModel):
    id: Annotated[Optional[str], Field(None, description="파일 또는 폴더 ID")]
    name: Annotated[Optional[str], Field(None, description="파일 또는 폴더 이름")]
    is_folder: Annotated[bool, Field(False, description="폴더 여부")]
    size_bytes: Annotated[Optional[int], Field(None, description="파일 크기")]
    created_time: Annotated[Optional[str], Field(None, description="생성 일시")]
    last_modified_time: Annotated[Optional[str], Field(None, description="마지막 수정 일시")]
    web_url: Annotated[Optional[str], Field(None, description="브라우저에서 열 수 있는 URL")]


class DriveItemDetail(DriveItemSummary):
    mime_type: Annotated[Optional[str], Field(None, description="MIME 타입")]
    download_url: Annotated[Optional[str], Field(None, description="다운로드 URL")]
