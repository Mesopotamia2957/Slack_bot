<!-- Generated: 2026-08-03 | Updated: 2026-08-03 -->

# Slack_bot

## Purpose

채용공고 알림 서비스의 **슬랙 클라이언트**. 슬랙 채널이나 DM에서 `!` 로 시작하는 명령을 받아
JerryBot_V2 API 를 호출하고, 결과를 슬랙 메시지로 돌려준다.

이 저장소는 크롤링을 하지 않는다. 크롤링과 DB 저장은 별도 저장소인 JerryBot_V2 의 배치가 담당하고,
여기서는 조회와 구독(키워드) 관리만 한다. Socket Mode 로 동작하므로 공개 URL 이나 웹훅 설정이 필요 없다.

## Key Files

| File | Description |
|------|-------------|
| `slack_command.py` | 진입점. slack_bolt 앱을 만들고 `handlers.register(app)` 로 리스너를 붙인 뒤 Socket Mode 로 실행한다 |
| `requirements.txt` | 의존 패키지 목록 |
| `.env.example` | 환경변수 템플릿. 복사해서 `.env` 로 쓴다 |
| `.env` | 실제 토큰이 든 파일. git 에 올리지 않는다 |
| `.gitignore` | `.env`, `.venv/`, `__pycache__/` 등 제외 목록 |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `jerrybot/` | 봇 로직 전체 — 설정, API 클라이언트, 메시지 포맷, 명령 처리 (see `jerrybot/AGENTS.md`) |

## For AI Agents

### Working In This Directory

- **기업을 추가할 때 이 저장소는 고치지 않는다.** 명령어는 `!` 로 시작하는 메시지를 단일 핸들러가
  받아 서버에 조회를 위임하는 구조라, 기업 추가는 JerryBot_V2 의 `Crawling_App/sites.py` 만 수정하면 된다.
  기업별 `@app.message` 데코레이터를 다시 만들지 말 것.
- `slack_command.py` 는 얇게 유지한다. 명령 처리 로직은 `jerrybot/handlers.py` 에 둔다.
- 실행 전 `.env` 가 있어야 한다. 없으면 `jerrybot/config.py` 가 `ConfigError` 를 던지며 즉시 멈춘다.
- `URI` 는 서버의 API 루트(예: `http://localhost:8000/api/`)를 가리켜야 한다. 뒤 슬래시는 config 가 보정한다.
- 슬랙에 보내는 모든 외부 HTTP 호출에는 타임아웃이 걸려 있어야 한다. `jerrybot/api.py` 를 우회해
  `requests` 를 직접 부르지 말 것.

### Testing Requirements

- 문법 검사: `.venv/bin/python -m compileall -q jerrybot slack_command.py`
- `handlers.dispatch(text, user_id, channel_id)` 는 슬랙 객체 없이 문자열만 주고받는 순수 함수라
  단위 테스트하기 쉽다. 새 명령을 넣으면 여기에 테스트를 붙인다.
- 실제 동작 확인에는 JerryBot_V2 서버가 떠 있어야 한다:
  `cd ../JerryBot_V2/JerryBot_V2 && ../.venv/bin/python manage.py runserver`
- 봇 실행: `python slack_command.py` (프로젝트 루트에서)

### Common Patterns

- 사용자에게 보일 오류는 `api.ApiError` 로 감싸 던지고, `dispatch()` 가 잡아 `⚠️` 를 붙여 응답한다.
- 예상 못 한 예외도 `dispatch()` 가 잡는다. 봇이 조용히 죽지 않게 하기 위한 것이므로 이 try 를 없애지 말 것.
- 공고 링크는 슬랙 mrkdwn `<url|제목>` 형식으로 넣어 제목 자체가 링크가 되게 한다.

## Dependencies

### Internal

- **JerryBot_V2 저장소** (`../JerryBot_V2/`) — 이 봇이 호출하는 REST API 제공. 응답 JSON 구조가 바뀌면
  `jerrybot/api.py` 와 `jerrybot/formatting.py` 를 함께 고쳐야 한다.

### External

- `slack_bolt` 1.18.1 — 슬랙 앱 프레임워크 (Socket Mode)
- `slack_sdk` 3.27.1 — slack_bolt 의존
- `requests` 2.31.0 — API 호출
- `python-dotenv` 1.0.1 — `.env` 로드
- `certifi` 2024.2.2 — macOS SSL 인증서 경로 문제 회피

<!-- MANUAL: 이 줄 아래에 직접 적은 메모는 재생성해도 보존됩니다 -->
