from typing import Annotated, Optional

from fastmcp import FastMCP

from app.common.graph_error_wrapper import graph_error_wrapper
from app.schemas.todo import TodoTask, TodoTaskList
from app.services.todo_service import TodoService
from app.tools.tool_context import get_request_current_user, resolve_graph_user


def register_todo_tools(mcp: FastMCP):
    todo_service = TodoService()

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def todo_list_task_lists(
        title: Annotated[Optional[str], "조회할 할 일 목록 이름입니다. 비우면 전체 목록을 조회합니다."] = None,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[TodoTaskList]:
        """Microsoft To Do의 할 일 목록을 조회합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 할 일 목록이나 작업 목록 ID를 모를 때 먼저 사용합니다.
        2. 반환된 id는 todo_list_tasks, todo_create_task에서 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await todo_service.list_task_lists(title, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=True)
    async def todo_list_tasks(
        task_list_id: Annotated[str, "할 일 목록 ID입니다. todo_list_task_lists 반환값의 id를 사용합니다."],
        top: Annotated[Optional[int], "최대 조회할 할 일 수입니다. 기본값은 10입니다."] = 10,
        user_email: Annotated[Optional[str], "조회 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> list[TodoTask]:
        """특정 할 일 목록의 할 일들을 조회합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 특정 목록 안의 할 일을 확인하고 싶어 할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await todo_service.list_tasks(task_list_id, top, query_email, query_company_cd)

    @mcp.tool()
    @graph_error_wrapper(as_list=False)
    async def todo_create_task(
        task_list_id: Annotated[str, "할 일을 추가할 목록 ID입니다."],
        title: Annotated[str, "새 할 일 제목입니다."],
        user_email: Annotated[Optional[str], "할 일을 생성할 사용자 이메일 주소입니다. 예: user@example.com"] = None,
        due_date: Annotated[Optional[str], "마감일입니다. YYYY-MM-DD 형식입니다."] = None,
    ) -> TodoTask:
        """새로운 할 일을 생성합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 할 일을 추가해달라고 요청할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await todo_service.create_task(task_list_id, title, query_email, query_company_cd, due_date)

    @mcp.tool()
    @graph_error_wrapper(as_list=False)
    async def todo_update_task(
        task_list_id: Annotated[str, "할 일이 들어 있는 목록 ID입니다."],
        task_id: Annotated[str, "수정할 할 일 ID입니다."],
        user_email: Annotated[Optional[str], "수정 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
        title: Annotated[Optional[str], "변경할 할 일 제목입니다."] = None,
        due_date: Annotated[Optional[str], "변경할 마감일입니다. YYYY-MM-DD 형식입니다."] = None,
        status: Annotated[Optional[str], "변경할 상태입니다. 예: notStarted, inProgress, completed"] = None,
        importance: Annotated[Optional[str], "변경할 중요도입니다. 예: low, normal, high"] = None,
    ) -> TodoTask:
        """기존 할 일을 부분 수정합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 할 일 제목, 마감일, 상태, 중요도를 바꾸고 싶어 할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await todo_service.update_task(
            task_list_id=task_list_id,
            task_id=task_id,
            user_email=query_email,
            company_cd=query_company_cd,
            title=title,
            due_date=due_date,
            status=status,
            importance=importance,
        )

    @mcp.tool()
    @graph_error_wrapper(as_list=False)
    async def todo_delete_task(
        task_list_id: Annotated[str, "할 일이 들어 있는 목록 ID입니다."],
        task_id: Annotated[str, "삭제할 할 일 ID입니다."],
        user_email: Annotated[Optional[str], "삭제 대상자의 이메일 주소입니다. 예: user@example.com"] = None,
    ) -> dict:
        """기존 할 일을 삭제합니다.

        [LLM 에이전트 가이드]
        1. 사용자가 특정 할 일을 삭제해달라고 요청할 때 사용합니다.
        """
        current_user = get_request_current_user()
        query_email, query_company_cd = resolve_graph_user(user_email, current_user)
        return await todo_service.delete_task(task_list_id, task_id, query_email, query_company_cd)
