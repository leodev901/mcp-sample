from typing import Annotated, Optional

from fastmcp import FastMCP

from app.common.graph_error_wrapper import graph_error_wrapper
from app.schemas.sharepoint import DriveItemDetail, DriveItemSummary
from app.services.sharepoint_service import SharePointService
from app.tools.tool_context import get_request_current_user, resolve_graph_user


def register_sharepoint_tools(mcp: FastMCP):
    sharepoint_service = SharePointService()

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def drive_list_files(
        folder_id: Annotated[Optional[str], "조회할 폴더 ID입니다. 비우면 루트 폴더를 조회합니다."] = None,
        top: Annotated[Optional[int], "최대 조회 건수입니다. 기본값은 15입니다."] = 15,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[DriveItemSummary]:
        """OneDrive 또는 SharePoint 개인 영역의 파일과 폴더 목록을 조회합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 드라이브 파일 목록이나 특정 폴더 내용을 요청하면 사용합니다.
        2. 반환된 id는 drive_get_file_info에서 상세 조회에 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await sharepoint_service.list_drive_files(folder_id, top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def drive_search_files(
        query: Annotated[str, "검색할 파일명 또는 본문 키워드입니다."],
        top: Annotated[Optional[int], "최대 조회 건수입니다. 기본값은 10입니다."] = 10,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[DriveItemSummary]:
        """OneDrive 또는 SharePoint에서 파일을 검색합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 특정 문서나 파일 위치를 찾고 싶어 할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await sharepoint_service.search_drive_files(query, top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=False)
    async def drive_get_file_info(
        item_id: Annotated[str, "상세 정보를 조회할 파일 또는 폴더 ID입니다."],
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> DriveItemDetail:
        """단일 파일 또는 폴더의 상세 정보와 다운로드 URL을 조회합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 특정 파일을 열거나 다운로드하고 싶어 할 때 사용합니다.
        2. 폴더는 다운로드 URL이 없을 수 있습니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await sharepoint_service.get_drive_file_info(item_id, query_email, query_company_cd)
