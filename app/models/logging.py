from typing import Optional
from uuid import UUID
from dattime import datetime
from pydantic import BaseModel, Field

class MCPToolLogRequest(BaseModel):
    trace_id: UUID = Field(..., description="HTTP request trace ID")
    tool_name: str = Field(..., description="Name of the MCP tool called")
    arguments: Optional[dict] = Field(default=None, description="Arguments passed to the tool")
    elapsed_ms: float = Field(..., description="Execution time in milliseconds")
    user_id: Optional[str] = Field(default=None, description="Identifier of the user")
    email: Optional[str] = Field(default=None, description="Email of the user")
    company_cd: Optional[str] = Field(default=None, description="Company code of the user")
    input: Optional[datetime] = Field(default=None, description="JSON string of the input data")
    output: Optional[datetime] = Field(default=None, description="JSON string of the output data")
    error_message: Optional[str] = Field(default=None, description="Error message if the call failed")
    status: str = Field(..., description="Success or error status")
    requested_at: datetime | None = None
    responded_at: datetime | None = None

