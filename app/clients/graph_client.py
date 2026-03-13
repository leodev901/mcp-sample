import httpx
import time 
import json
from loguru import logger 


from fastmcp.server.dependencies import get_http_request 

from app.core.config import settings
from app.models.user_info import UserInfo

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL_TPL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

DEFAULT_USER_EMAIL = ""


def logging_message(
        status_code:int,
        method:str,
        trace_id:str,
        elapsed_ms:float | None= None,
        current_user:UserInfo | None= None,  
        req_json: dict | None= None, 
        resp_json: dict | None= None,
        error_message: str | None = None,
)->None:
    message=f"[GraphAPI Request] >>> trace_id={trace_id}"
    message+=f" status_code={status_code}"
    message+=f" method={method}"
    latency_str = f"{elapsed_ms:.1f}" if elapsed_ms is not None else "0.0"
    message+=f" elapsed_ms={latency_str}"
    message+=f" email={current_user.email if current_user else '-'}"
    message+=f" company_cd={current_user.company_cd if current_user else '-'}"
    message+=f"\n request={req_json if req_json else '-'}"
    if resp_json is not None :
        message+=f"\n response={resp_json if resp_json else '-'}"
    if error_message is not None :
        message+=f"\n error={error_message}"        
    
    if(status_code==200):
        logger.info(message)
    else:
        logger.error(message)

async def get_access_token(company_cd: str = "leodev901") -> str:
    """Return (access_token, default_user_email)."""

    ms365_config = settings.get_m365_config(company_cd)
    tenant_id = ms365_config["tenant_id"]
    client_id = ms365_config["client_id"]
    client_secret = ms365_config["client_secret"]
    DEFAULT_USER_EMAIL = ms365_config.get("default_user_email","admin@leodev901.onmicrosoft.com")

    if not client_id or not client_secret or not tenant_id:
        raise ValueError(f"MS365 config is incomplete for company_cd='{company_cd}'")

    token_url = TOKEN_URL_TPL.format(tenant_id=tenant_id)
    data = {
        "client_id": client_id,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    
    try:
        print(f"get access token for '{company_cd}'")
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(token_url, data=data)
            resp.raise_for_status()
            return resp.json()["access_token"]
    except Exception as e:
        raise e


async def graph_request(
    method: str,
    path: str,
    user_email: str | None = None,
    json_body: dict | None = None,
    company_cd: str = "leodev901",
) -> dict:
    """Common wrapper for Microsoft Graph user-scoped APIs."""

    # 로깅을 위한 컨텍스트 확보
    try:
        req = get_http_request()
        trace_id = getattr(req.state, "trace_id", "internal")
        current_user = getattr(req.state, "current_user", None)
    except:
        trace_id = "unknown"
    

    token = await get_access_token(company_cd)
    email = user_email or DEFAULT_USER_EMAIL

    if not email:
        raise ValueError("user_email is required or default_user_email must be configured")

    url = f"{GRAPH_BASE}/users/{email}{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}


    start_time = time.perf_counter() # 타이머 시작
    req_body = {
        "method": method,
        "url": url,
        "body": json_body,
    } or None
    req_json = json.dumps(req_body, ensure_ascii=False, indent=2)
    # logger.info(f"[GraphAPI Request] Trace={trace_id} | User={current_user.user_id} \n Request={req_json}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(method.upper(), url, headers=headers, json=json_body)
            resp.raise_for_status()
            resp_json = json.dumps(resp.json(), ensure_ascii=False, indent=2)
            status_code = resp.status_code
            error_detail = None
            return resp.json()
    except Exception as e:
        status_code = 500
        resp_json = None
        error_detail = f"{type(e).__name__}: {e}"
        raise e
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logging_message(
            status_code=status_code,
            trace_id=trace_id,
            elapsed_ms=elapsed_ms,
            current_user=current_user,
            method=method,
            req_json=req_json,
            resp_json=resp_json,
            error_message=error_detail,
        )


    
