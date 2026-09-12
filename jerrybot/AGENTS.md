<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-08-03 | Updated: 2026-08-03 -->

# jerrybot

## Purpose

슬랙봇 로직 전체를 담은 패키지. 원래 `slack_command.py` 파일 하나에 기업별 핸들러 15개가
복사-붙여넣기로 들어 있었으나, 설정 / API 호출 / 메시지 포맷 / 명령 처리 네 갈래로 분리했다.

레이어가 나뉜 이유는 `handlers.py` 가 HTTP 나 슬랙 SDK 를 몰라도 되게 하기 위해서다.
`dispatch()` 는 문자열을 받아 문자열을 돌려주므로 슬랙 없이 테스트할 수 있다.

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | 패키지 선언 및 역할 설명 |
| `config.py` | `.env` 로드와 검증. 필수 값이 없으면 `ConfigError` 를 던져 기동 단계에서 실패시킨다 |
| `api.py` | JerryBot_V2 REST API 클라이언트. 모든 요청에 타임아웃을 걸고 오류를 `ApiError` 로 정규화한다 |
| `formatting.py` | 슬랙 mrkdwn 메시지 생성. 공고 제목이 링크가 되도록 `<url\|제목>` 을 만든다. `HELP` 문구도 여기 있다 |
| `handlers.py` | 명령 해석과 처리. `COMMANDS` 표에 명령어를 등록하고 `dispatch()` 가 라우팅한다 |

## For AI Agents

### Working In This Directory

- **새 명령을 추가하려면** `handlers.py` 에 `cmd_*` 함수를 만들고 `COMMANDS` 딕셔너리에 등록한다.
  핸들러 시그니처는 `(command=, args=, user_id=, channel_id=)` 를 키워드로 받고 쓰지 않는 것은
  `**_` 로 흘려보내는 형태다.
- `COMMANDS` 에 없는 명령은 자동으로 `cmd_company` 로 떨어져 기업명으로 해석된다. 즉 `!네이버` 같은
  기업 조회는 별도 등록이 필요 없다. 서버가 404 를 주면 `NotFoundError` 로 안내 메시지를 돌려준다.
- **DM 채널일 때만 `channel_id` 를 서버에 저장한다** (`_is_dm()`, 채널 ID 가 `D` 로 시작). 공개 채널
  ID 를 알림 채널로 저장하면 개인 키워드 알림이 채널에 공개된다. 이 검사를 우회하지 말 것.
- `api.py` 에 새 함수를 넣을 때는 반드시 `_request()` 를 거치게 한다. `requests` 를 직접 호출하면
  타임아웃과 API 키 헤더가 빠진다.
- 사용자에게 보일 오류 문구는 `ApiError` 메시지에 그대로 담는다. `dispatch()` 가 앞에 `⚠️` 를 붙인다.

### Testing Requirements

- `dispatch()` 는 순수 함수다. `api` 모듈을 monkeypatch 하면 서버 없이 명령별 응답을 검증할 수 있다.
- 문법 검사: `python -m compileall -q .`
- 실제 호출 검증에는 JerryBot_V2 서버가 필요하다.

### Common Patterns

- 서버 응답 JSON 키(`count`, `results`, `keywords`, `added`, `removed`, `notify_enabled` 등)에
  직접 의존한다. 서버의 `serializers.py` 나 뷰 응답을 바꾸면 여기도 함께 고쳐야 한다.
- 긴 목록은 `config.MAX_ITEMS` 로 잘라 보내고, 남은 건수를 안내 문구로 덧붙인다.
  슬랙 메시지 길이 제한(약 4000자)을 넘기지 않기 위한 것이다.
- 명령어 별칭은 `COMMANDS` 에 같은 함수를 여러 키로 등록해 지원한다 (`도움말`/`help`/`사용법`).

## Dependencies

### Internal

- `../slack_command.py` — `handlers.register(app)` 와 `config.BOT_TOKEN` / `config.APP_TOKEN` 을 사용
- JerryBot_V2 의 `Crawling_App/urls.py` 경로와 `Crawling_App/views.py` 응답 형식

### External

- `requests` — `api.py` 의 HTTP 호출
- `python-dotenv` — `config.py` 의 `.env` 로드
- `slack_bolt` — `handlers.register()` 가 받는 `app` 객체의 타입 (직접 import 하지는 않는다)

<!-- MANUAL: 이 줄 아래에 직접 적은 메모는 재생성해도 보존됩니다 -->
