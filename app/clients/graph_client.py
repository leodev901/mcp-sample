import httpx

from app.core.config import settings

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL_TPL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

DEFAULT_USER_EMAIL = ""

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

    token = await get_access_token(company_cd)
    email = user_email or DEFAULT_USER_EMAIL

    if not email:
        raise ValueError("user_email is required or default_user_email must be configured")

    url = f"{GRAPH_BASE}/users/{email}{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(method.upper(), url, headers=headers, json=json_body)
        resp.raise_for_status()
        return resp.json()
