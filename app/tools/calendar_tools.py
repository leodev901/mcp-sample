from fastmcp import FastMCP

from loguru import logger
from typing import Annotated,Optional
from datetime import datetime

from app.clients.graph_client import graph_request

current_time = datetime.now().isoformat(timespec="seconds")


def register_calendar_tools(mcp: FastMCP):
    

    @mcp.tool()
    async def check_company_token(company_cd:str ):
        raise NotImplementedError()


    @mcp.tool(description=f"""MS365 Outllok 캘린더 일정을 조회합니다.

            [LLM 에이전트 가이드]
            1. 사용자가 "일정 조회해줘", "캘린더 확인해줘" 와 같이 일정을 확인해달라는 요청이 오면, 이 도구를 사용하여 MS365의 일정(Caneldar)을 조회합니다.
            2. 일정을 조회하기 위해서는 사용자로부터 '시작일','종료일','사용자 이메일' 정보를 필수로 받아야 합니다.
                만약, 사용자가 '이번주'나 '다음주'와 같이 상대적인 기간을 명시하면 오늘날짜 "{current_time}"를 기준으로 시작일과 종료일을 계산하여 채워줘야 합니다. 

            Args:
                start_date (str): 조회 시작일 (ISO 8601, 예: 2026-03-01T:00:00:00)
                end_date (str): 조회 종료일 (ISO 8601, 예: 2026-03-31T:23:59:59)
                user_emial (str): 일정 대상자의 이메일주소 입니다. 예: no-reply@microsoft.com
                company_cd (str): 일정 대상자의 회사코드 입니다. 예: skcc 또는 skt 

            Returns:
                list[dict]: 일정 목록 정보를 반환합니다.
              """)
    async def list_calendar_events(
        start_date: Annotated[str,"조회 시작일 (ISO 8601, 예: 2026-03-01T00:00:00)"],
        end_date: Annotated[str,"조회 종료일 (ISO 8601, 예: 2026-03-31T23:59:59)"],
        user_email: Annotated[str,"일정 대상자의 이메일주소 입니다. 예: no-reply@microsoft.com"]="admin@leodev901.onmicrosoft.com",
        top: Annotated[Optional[int],"최대 조회 건수 (기본 10)"]=10,
        company_cd: Annotated[Optional[str],"일정 대상자의 회사코드 입니다. 예: skcc 또는 skt"]="leodev901",
    ) -> list[dict]:
        """MS365 Outllok 캘린더 일정을 조회합니다.            
        """

        # https://graph.microsoft.com/v1.0/users/admin@leodev901.onmicrosoft.com
        # /calendarView
        # ?startDateTime=2026-03-01T00:00:00
        # &endDateTime=2026-03-31T23:59:59
        # &$top=10
        # &$orderby=start/dateTime
        # &$select=id,subject,start,end,location,organizer,isOnlineMeeting,webLink

        path=(
            f"/calendarView"
            f"?startDateTime={start_date}"
            f"&endDateTime={end_date}"
            f"&$top={top}"
            f"&$orderby=start/dateTime"
            f"&$select=id,subject,start,end,location,organizer,isOnlineMeeting,webLink"
        )
        result = await graph_request(
            method="GET",
            path=path,
            user_email=user_email,
            company_cd=company_cd
        )

        
        return [
         {
            "id" : ev.get("id"),
            "subject" : ev.get("subject"),
            "start" : ev.get("start"),
            "end" : ev.get("end"),
            "location" : ev.get("location",{}).get("displayName",""),
            "organizer" : ev.get("organizer",{}).get("emailAddress",{}).get("address",""),
            "weblink" : ev.get("weblink"),
         } for ev in result.get("vlaue",[])
        ]

