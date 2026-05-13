from urllib.parse import quote

from pydantic import TypeAdapter

from app.clients.graph_client import graph_request
from app.schemas.sharepoint import DriveItemDetail, DriveItemSummary


class SharePointService:
    async def list_drive_files(self, folder_id: str | None, top: int | None, user_email: str, company_cd: str) -> list[DriveItemSummary]:
        # folder_id가 없으면 루트 폴더, 있으면 해당 폴더의 children을 조회합니다.
        query_top = top if top is not None and top > 0 else 15
        path = f"/drive/items/{folder_id}/children" if folder_id else "/drive/root/children"
        result = await graph_request(method="GET", path=f"{path}?$top={query_top}", user_email=user_email, company_cd=company_cd)
        return TypeAdapter(list[DriveItemSummary]).validate_python([self._to_summary(item) for item in result.get("value", [])])

    async def search_drive_files(self, query: str, top: int | None, user_email: str, company_cd: str) -> list[DriveItemSummary]:
        # 검색어는 URL 경로에 들어가므로 quote로 안전하게 인코딩합니다.
        query_top = top if top is not None and top > 0 else 10
        encoded_query = quote(query, safe="")
        result = await graph_request(
            method="GET",
            path=f"/drive/root/search(q='{encoded_query}')?$top={query_top}",
            user_email=user_email,
            company_cd=company_cd,
        )
        return TypeAdapter(list[DriveItemSummary]).validate_python([self._to_summary(item) for item in result.get("value", [])])

    async def get_drive_file_info(self, item_id: str, user_email: str, company_cd: str) -> DriveItemDetail:
        # 상세 조회는 다운로드 URL과 MIME 타입까지 포함합니다.
        item = await graph_request(method="GET", path=f"/drive/items/{item_id}", user_email=user_email, company_cd=company_cd)
        summary = self._to_summary(item)
        summary.update(
            {
                "mime_type": item.get("file", {}).get("mimeType"),
                "download_url": item.get("@microsoft.graph.downloadUrl"),
            }
        )
        return DriveItemDetail.model_validate(summary)

    def _to_summary(self, item: dict) -> dict:
        # Graph DriveItem 원본에서 도구 반환에 필요한 공통 필드만 추립니다.
        return {
            "id": item.get("id"),
            "name": item.get("name"),
            "is_folder": "folder" in item,
            "size_bytes": item.get("size"),
            "created_time": item.get("createdDateTime"),
            "last_modified_time": item.get("lastModifiedDateTime"),
            "web_url": item.get("webUrl"),
        }
