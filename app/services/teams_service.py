from pydantic import TypeAdapter

from app.clients.graph_client import graph_request
from app.schemas.teams import TeamsChatMessage, TeamsChatSummary, TeamsSendMessageResult


class TeamsService:
    async def list_chats(self, top: int | None, user_email: str, company_cd: str) -> list[TeamsChatSummary]:
        # 최근 채팅방을 가져오고 lastMessagePreview만 사용자 응답에 필요한 형태로 줄입니다.
        query_top = top if top is not None and top > 0 else 10
        result = await graph_request(
            method="GET",
            path=f"/chats?$top={query_top}&$expand=lastMessagePreview",
            user_email=user_email,
            company_cd=company_cd,
        )
        chats = [
            {
                "id": chat.get("id"),
                "topic": chat.get("topic") or "(제목 없는 채팅방)",
                "chat_type": chat.get("chatType"),
                "last_message_preview": chat.get("lastMessagePreview", {}).get("body", {}).get("content"),
                "last_updated": chat.get("lastUpdatedDateTime"),
            }
            for chat in result.get("value", [])
        ]
        return TypeAdapter(list[TeamsChatSummary]).validate_python(chats)

    async def list_chat_messages(self, chat_id: str, top: int | None, user_email: str, company_cd: str) -> list[TeamsChatMessage]:
        # 메시지는 최신순으로 조회해 대화 요약에 필요한 필드만 반환합니다.
        query_top = top if top is not None and top > 0 else 15
        result = await graph_request(
            method="GET",
            path=f"/chats/{chat_id}/messages?$top={query_top}&$orderby=createdDateTime desc",
            user_email=user_email,
            company_cd=company_cd,
        )
        messages = [
            {
                "id": message.get("id"),
                "sender": message.get("from", {}).get("user", {}).get("displayName"),
                "created_time": message.get("createdDateTime"),
                "content": message.get("body", {}).get("content"),
                "type": message.get("messageType"),
            }
            for message in result.get("value", [])
        ]
        return TypeAdapter(list[TeamsChatMessage]).validate_python(messages)

    async def send_chat_message(self, chat_id: str, content: str, user_email: str, company_cd: str) -> TeamsSendMessageResult:
        # Teams 메시지 전송 API는 body.contentType/content 구조를 요구합니다.
        payload = {"body": {"contentType": "html", "content": content}}
        result = await graph_request(
            method="POST",
            path=f"/chats/{chat_id}/messages",
            json_body=payload,
            user_email=user_email,
            company_cd=company_cd,
        )
        return TeamsSendMessageResult.model_validate(
            {"status": "success", "message_id": result.get("id"), "created_time": result.get("createdDateTime")}
        )
