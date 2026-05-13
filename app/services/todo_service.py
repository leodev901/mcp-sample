from typing import Optional

from pydantic import TypeAdapter

from app.clients.graph_client import graph_request
from app.schemas.todo import TodoTask, TodoTaskList


class TodoService:
    async def list_task_lists(self, title: Optional[str], user_email: str, company_cd: str) -> list[TodoTaskList]:
        # title이 있으면 Graph filter로 특정 할 일 목록만 좁힙니다.
        path = "/todo/lists"
        if title:
            path += f"?$filter=displayName eq '{title}'"
        result = await graph_request(method="GET", path=path, user_email=user_email, company_cd=company_cd)
        return TypeAdapter(list[TodoTaskList]).validate_python(result.get("value", []))

    async def list_tasks(self, task_list_id: str, top: int | None, user_email: str, company_cd: str) -> list[TodoTask]:
        # 목록 내 할 일을 최신 생성순으로 조회합니다.
        query_top = top if top is not None and top > 0 else 10
        path = f"/todo/lists/{task_list_id}/tasks?$top={query_top}&$orderby=createdDateTime desc"
        result = await graph_request(method="GET", path=path, user_email=user_email, company_cd=company_cd)
        return TypeAdapter(list[TodoTask]).validate_python(result.get("value", []))

    async def create_task(
        self,
        task_list_id: str,
        title: str,
        user_email: str,
        company_cd: str,
        due_date: Optional[str] = None,
    ) -> TodoTask:
        # dueDateTime은 Graph가 요구하는 dateTime/timeZone 객체로 구성합니다.
        payload: dict = {"title": title}
        if due_date:
            payload["dueDateTime"] = {"dateTime": f"{due_date}T00:00:00", "timeZone": "Asia/Seoul"}
        result = await graph_request(
            method="POST",
            path=f"/todo/lists/{task_list_id}/tasks",
            json_body=payload,
            user_email=user_email,
            company_cd=company_cd,
        )
        return TodoTask.model_validate(result)

    async def update_task(
        self,
        task_list_id: str,
        task_id: str,
        user_email: str,
        company_cd: str,
        title: Optional[str] = None,
        due_date: Optional[str] = None,
        status: Optional[str] = None,
        importance: Optional[str] = None,
    ) -> TodoTask:
        # PATCH는 사용자가 전달한 필드만 반영합니다.
        payload: dict = {}
        if title is not None:
            payload["title"] = title
        if due_date is not None:
            payload["dueDateTime"] = {"dateTime": f"{due_date}T00:00:00", "timeZone": "Asia/Seoul"}
        if status is not None:
            payload["status"] = status
        if importance is not None:
            payload["importance"] = importance
        if not payload:
            raise ValueError("수정할 할 일 항목이 하나 이상 필요합니다.")

        result = await graph_request(
            method="PATCH",
            path=f"/todo/lists/{task_list_id}/tasks/{task_id}",
            json_body=payload,
            user_email=user_email,
            company_cd=company_cd,
        )
        return TodoTask.model_validate(result)

    async def delete_task(self, task_list_id: str, task_id: str, user_email: str, company_cd: str) -> dict:
        # 삭제 성공 시 Graph는 본문을 주지 않으므로 도구용 성공 메시지를 반환합니다.
        await graph_request(method="DELETE", path=f"/todo/lists/{task_list_id}/tasks/{task_id}", user_email=user_email, company_cd=company_cd)
        return {"status": "success", "task_list_id": task_list_id, "task_id": task_id, "message": "할 일을 삭제했습니다."}
