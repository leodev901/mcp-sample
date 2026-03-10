# MCP Sample (FastMCP)

Microsoft 365 일정 조회를 중심으로 구성한 FastMCP 서버 샘플입니다.  
현재 버전은 HTTP 요청 헤더에서 사용자 토큰을 읽고, MCP tool 실행까지 같은 요청 컨텍스트로 연결하는 흐름을 포함합니다.

## 현재 핵심 기능
- `/mcp` 경로로 Streamable HTTP 기반 MCP 서버 제공
- HTTP 미들웨어에서 `x-request-id`와 `mcp_user_token` 처리
- JWT 토큰으로 사용자 정보(`UserInfo`)를 해석해 MCP context에 저장
- MCP tool 미들웨어에서 `trace_id` 기준 실행 로그 기록
- `calendar_tools`에서 내 일정 조회 및 일반 일정 조회 제공
- 일정 목록 반환 시 참석자, 종일 일정 여부, busy/free 상태, 온라인 회의 정보 포함

## 프로젝트 구조
```text
app/
  main.py                     # FastMCP 서버 조립 및 HTTP app 생성

  core/
    http_middleware.py        # trace_id / user_token / current_user 설정
    mcp_midleware.py          # MCP tool 호출 로그
    mcp_context.py            # 요청 단위 context 저장소
    config.py                 # .env 및 회사별 MS365 설정

  clients/
    http_client.py            # 공통 Async HTTP 클라이언트
    graph_client.py           # Microsoft Graph API 호출

  security/
    jwt_auth.py               # JWT 검증 및 사용자 조회
    key_cache.py              # 공개키 캐시

  tools/
    calendar_tools.py         # 일정 조회 MCP tools
```

## 요청 처리 흐름
1. 클라이언트가 `/mcp`로 요청을 보냅니다.
2. `HttpLoggingMiddleware`가 `x-request-id`를 만들거나 재사용합니다.
3. `mcp_user_token`이 있으면 `jwt_auth.py`에서 사용자 정보를 해석합니다.
4. `mcp_context.py`에 `trace_id`, `user_token`, `current_user`를 저장합니다.
5. MCP tool 실행 시 `MCPLoggingMiddleware`가 같은 `trace_id`로 로그를 남깁니다.
6. `calendar_tools.py`는 필요 시 context의 `current_user`를 읽어 기본 이메일과 회사코드를 결정합니다.

## 일정 조회 반환 필드
현재 일정 조회 tool은 아래 필드를 중심으로 반환합니다.

- `id`
- `subject`
- `start`
- `end`
- `location`
- `organizer`
- `is_all_day`
- `show_as`
- `is_online_meeting`
- `online_meeting_url`
- `attendees`
- `weblink`

`attendees`는 아래와 같은 최소 구조로 정리해 반환합니다.

```json
[
  {
    "email": "user@example.com",
    "name": "User",
    "type": "required",
    "response": "accepted"
  }
]
```

## 실행 방법
### 로컬 개발
```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8002
```

### MCP Inspector
```bash
npx @modelcontextprotocol/inspector
```

권장 연결 정보:
- Transport Type: `streamable-http`
- URL: `http://127.0.0.1:8002/mcp`

## 환경 변수 예시
```env
LOG_LEVEL=DEBUG
AUTH_JWT_USER_TOKEN=false
MS365_CONFIGS={"leodev901":{"tenant_id":"...","client_id":"...","client_secret":"..."}}
```

### 주요 환경 변수
- `LOG_LEVEL`: 로그 레벨
- `AUTH_JWT_USER_TOKEN`: `true`면 실제 JWT 검증 경로 사용, `false`면 샘플 사용자 정보 사용
- `MS365_CONFIGS`: 회사별 Microsoft 365 설정 JSON

## 현재 구현 메모
- `list_my_calendar_events`는 MCP context의 현재 사용자 정보를 사용할 수 있습니다.
- `mcp_user_token`이 없으면 기본값 기반 조회로 떨어질 수 있습니다.
- 헤더 전체 로그와 토큰 로그는 운영 환경에서는 마스킹 또는 제거가 필요합니다.

## 한 줄 요약
이 프로젝트는 `HTTP request -> 사용자 컨텍스트 해석 -> MCP tool 실행` 흐름을 가진 FastMCP 기반 Microsoft 365 일정 조회 서버입니다.
