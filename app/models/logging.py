from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class MCPToolLogRequest(BaseModel):
    # trace_id는 HTTP 헤더에서 들어온 문자열이므로 UUID가 아닌 str로 받습니다.
    trace_id: str = Field(..., description="HTTP request trace ID")
    tool_name: str = Field(..., description="Name of the MCP tool called")
    arguments: Optional[dict] = Field(default=None, description="Arguments passed to the tool")
    elapsed_ms: float = Field(..., description="Execution time in milliseconds")
    user_id: Optional[str] = Field(default=None, description="Identifier of the user")
    email: Optional[str] = Field(default=None, description="Email of the user")
    company_cd: Optional[str] = Field(default=None, description="Company code of the user")
    # input/output은 JSON 문자열을 저장하므로 datetime이 아니라 str 타입을 사용합니다.
    input: Optional[str] = Field(default=None, description="JSON string of the input data")
    output: Optional[str] = Field(default=None, description="JSON string of the output data")
    error_message: Optional[str] = Field(default=None, description="Error message if the call failed")
    status: str = Field(..., description="Success or error status")
    requested_at: datetime | None = None
    responded_at: datetime | None = None

