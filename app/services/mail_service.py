from typing import Optional
from urllib.parse import quote

from pydantic import TypeAdapter

from app.clients.graph_client import graph_request
from app.schemas.mail import MailDetail, MailSummary


class MailService:
    async def get_recent_emails(self, top: int | None, user_email: str, company_cd: str) -> list[MailSummary]:
        # 받은 편지함의 최신 메일을 수신 시각 내림차순으로 조회합니다.
        query_top = top if top is not None and top > 0 else 10
        path = f"/mailFolders/inbox/messages?$top={query_top}&$orderby=receivedDateTime desc"
        return await self._list_messages(path, user_email, company_cd)

    async def get_unread_emails(self, top: int | None, user_email: str, company_cd: str) -> list[MailSummary]:
        # 읽지 않은 메일만 필터링합니다.
        query_top = top if top is not None and top > 0 else 10
        path = f"/mailFolders/inbox/messages?$filter=isRead eq false&$top={query_top}&$orderby=receivedDateTime desc"
        return await self._list_messages(path, user_email, company_cd)

    async def get_important_or_flagged_emails(self, top: int | None, user_email: str, company_cd: str) -> list[MailSummary]:
        # 중요도 high 또는 followup 플래그가 있는 메일을 찾습니다.
        query_top = top if top is not None and top > 0 else 10
        path = (
            "/mailFolders/inbox/messages"
            "?$filter=importance eq 'high' or flag/flagStatus eq 'flagged'"
            f"&$top={query_top}&$orderby=receivedDateTime desc"
        )
        return await self._list_messages(path, user_email, company_cd)

    async def search_emails_by_keyword(self, keyword: str, top: int | None, user_email: str, company_cd: str) -> list[MailSummary]:
        # Graph $search는 큰따옴표 query를 요구하므로 키워드를 URL 인코딩합니다.
        query_top = top if top is not None and top > 0 else 10
        encoded = quote(f'"{keyword}"', safe="")
        path = f"/messages?$search={encoded}&$top={query_top}"
        return await self._list_messages(path, user_email, company_cd, prefer_eventual=True)

    async def search_emails_by_sender(self, sender: str, top: int | None, user_email: str, company_cd: str) -> list[MailSummary]:
        # from/emailAddress/address와 from/emailAddress/name 둘 다 대상으로 검색합니다.
        query_top = top if top is not None and top > 0 else 10
        escaped = sender.replace("'", "''")
        path = (
            "/messages"
            f"?$filter=contains(from/emailAddress/address,'{escaped}') or contains(from/emailAddress/name,'{escaped}')"
            f"&$top={query_top}&$orderby=receivedDateTime desc"
        )
        return await self._list_messages(path, user_email, company_cd)

    async def search_emails_by_attachment(
        self,
        top: int | None,
        user_email: str,
        company_cd: str,
        file_name_keyword: Optional[str] = None,
    ) -> list[MailSummary]:
        # 첨부 여부는 메시지 필드로 필터링하고 파일명 세부 검색은 상세 조회 도구와 조합하도록 합니다.
        query_top = top if top is not None and top > 0 else 10
        path = f"/messages?$filter=hasAttachments eq true&$top={query_top}&$orderby=receivedDateTime desc"
        messages = await self._list_messages(path, user_email, company_cd)
        if not file_name_keyword:
            return messages

        # 파일명 키워드는 메시지별 첨부 목록을 확인해야 하므로 제한된 결과 안에서 추가 필터링합니다.
        matched: list[MailSummary] = []
        for message in messages:
            if not message.id:
                continue
            detail = await self.get_email_detail(message.id, user_email, company_cd)
            if any(file_name_keyword.lower() in (attachment.name or "").lower() for attachment in detail.attachments or []):
                matched.append(message)
        return matched

    async def get_sent_emails(self, top: int | None, user_email: str, company_cd: str) -> list[MailSummary]:
        # 보낸 편지함은 sentDateTime 기준 최신순으로 조회합니다.
        query_top = top if top is not None and top > 0 else 10
        path = f"/mailFolders/sentitems/messages?$top={query_top}&$orderby=sentDateTime desc"
        return await self._list_messages(path, user_email, company_cd)

    async def get_email_detail(self, message_id: str, user_email: str, company_cd: str) -> MailDetail:
        # 상세 조회와 첨부 조회를 합쳐 한 번에 사용할 수 있는 반환 형태를 만듭니다.
        message = await graph_request(method="GET", path=f"/messages/{message_id}", user_email=user_email, company_cd=company_cd)
        attachments = await graph_request(
            method="GET",
            path=f"/messages/{message_id}/attachments",
            user_email=user_email,
            company_cd=company_cd,
        )
        parsed = self._to_summary_dict(message)
        parsed["body"] = message.get("body")
        parsed["attachments"] = attachments.get("value", [])
        return MailDetail.model_validate(parsed)

    async def _list_messages(
        self,
        path: str,
        user_email: str,
        company_cd: str,
        prefer_eventual: bool = False,
    ) -> list[MailSummary]:
        # 메일 목록 조회의 공통 Graph 호출과 스키마 검증을 한 곳에 모읍니다.
        headers = {"ConsistencyLevel": "eventual"} if prefer_eventual else None
        result = await graph_request(
            method="GET",
            path=path,
            user_email=user_email,
            company_cd=company_cd,
            custom_headers=headers,
        )
        return TypeAdapter(list[MailSummary]).validate_python([self._to_summary_dict(message) for message in result.get("value", [])])

    def _to_summary_dict(self, message: dict) -> dict:
        # Graph Message 원본에서 LLM 응답에 자주 쓰는 핵심 필드만 추립니다.
        sender_info = message.get("from", {}).get("emailAddress") or message.get("sender", {}).get("emailAddress") or {}
        return {
            "id": message.get("id"),
            "subject": message.get("subject"),
            "sender": {"name": sender_info.get("name"), "address": sender_info.get("address")},
            "received_date_time": message.get("receivedDateTime"),
            "sent_date_time": message.get("sentDateTime"),
            "body_preview": message.get("bodyPreview"),
            "importance": message.get("importance"),
            "is_read": message.get("isRead"),
            "has_attachments": message.get("hasAttachments"),
            "web_link": message.get("webLink"),
        }
