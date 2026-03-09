# MCP Sample (FastMCP)

엔터프라이즈 환경을 고려한 FastMCP 서버 샘플입니다.
핵심 목표는 기능 추가 속도와 운영 안정성의 균형입니다.

## 문제 정의
초기 단일 파일 구조는 빠르게 시작할 수 있지만, 기능이 늘면 다음 문제가 생깁니다.
- `main.py` 비대화 (툴 등록/초기화/실행 코드 혼재)
- 공통 코드 중복 (인증, 설정, 로깅, HTTP 호출)
- 환경별 실행/import 불일치 (로컬 vs Docker/K8s)

## 접근 방법
현재 프로젝트는 "과하지 않은 모듈화"를 기준으로 정리합니다.
- `main.py`: 조립(Composition Root)과 실행 진입점만 담당
- `core`: 전역 공통(설정/로깅/미들웨어)
- `clients`: 외부 시스템 연동(HTTP/Graph)
- `tools`: MCP 도메인 툴 등록(mail/calendar/todo/sharepoint/teams)

## 프로젝트 구조 (합의안)
```text
app/
  main.py                     # 서버 생성/툴 등록/ASGI app 반환
  server.py                   # 실험/샘플 엔트리(선택)

  core/
    config.py                 # Settings(.env 로딩, 회사별 MS365 설정)
    logger_config.py          # 로깅 설정
    http_middleware.py        # HTTP 레벨 미들웨어
    mcp_midleware.py          # MCP tool 호출 레벨 미들웨어

  clients/
    http_client.py            # 공통 HTTP 호출 유틸(확장 포인트)
    graph_client.py           # Microsoft Graph API 클라이언트

  tools/
    mail_tools.py
    calendar_tools.py
    to_do_tools.py
    sharepoint_tools.py
    teams_tools.py

docs/
  SKILL_GUIDE.md
  CODE_GUIDE.md
  EXAMPLE_GUIDE.md
  DIAGRAM_GUIDE.md
```

## 설계 컨셉
- 경량 모듈화: 폴더를 과도하게 쪼개지 않고 역할 단위로만 분리
- 절대 import: `from app...` 형태로 통일
- 실행 일관성: 로컬/컨테이너/쿠버네티스에서 동일한 엔트리 사용
- 미들웨어 분리: HTTP 관점과 MCP Tool 관점을 분리해서 관측성 확보

## 실행 방법
### 로컬 개발
```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe -m app.main
```

```bash
npx @modelcontextprotocol/inspector
```

### 운영 권장 (uvicorn)
```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8002
```

### Docker/K8s 권장 커맨드
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## import 규칙
- 권장: `from app.tools.calendar_tools import register_calendar_tools`
- 비권장: `from tools.calendar_tools import ...`

이유:
- 작업 디렉터리/실행 방식에 덜 민감하고, 배포 환경에서 경로 문제가 줄어듭니다.

## 미들웨어 규칙
- HTTP 미들웨어: 요청/응답, 헤더, request_id, 상태코드 로깅
- MCP 미들웨어: tool 이름, 인자 키, 실행 시간, 예외 로깅

둘은 레이어가 달라서 운영에서는 보통 함께 사용합니다.

## 검증 체크리스트
- `python -m app.main`로 import 오류 없이 기동되는가
- `uvicorn app.main:app`로 동일하게 기동되는가
- `tools` 추가 시 `main.py` 변경 최소화가 지켜지는가
- `core`에 도메인 로직이 섞이지 않았는가

## 한 줄 요약
이 프로젝트는 `main.py(조립) + core(공통) + clients(외부연동) + tools(도메인)`의 경량 구조로, 엔터프라이즈 운영(Docker/K8s)까지 고려한 FastMCP 기준선입니다.