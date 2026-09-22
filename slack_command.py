"""봇 진입점. 이 파일을 실행하면 슬랙 연결이 뜬다 (`python slack_command.py`).

Socket Mode 를 쓴다 — 슬랙이 우리 서버로 들어오는 게 아니라, 봇이 슬랙으로 나가서
연결을 유지하는 방식이다. 덕분에 인바운드 포트를 열지 않아도 되고 공인 IP 도 필요 없다
(서버에서 slack-bot 컨테이너에 포트가 하나도 열려 있지 않은 이유).

토큰이 두 개인 이유: BOT_TOKEN(xoxb-)은 슬랙 API 호출용, APP_TOKEN(xapp-)은
Socket Mode 연결을 맺는 용도다.
"""

import logging
import os

import certifi
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from jerrybot import config, handlers

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')

# 셸 설정이 없는 환경(cron·컨테이너)에서 시스템 인증서를 못 찾아 SSL 검증이 실패한다.
# 라이브러리가 읽기 전에 미리 박아 둔다.
os.environ['SSL_CERT_FILE'] = certifi.where()

app = App(token=config.BOT_TOKEN)
handlers.register(app)


if __name__ == '__main__':
    SocketModeHandler(app, config.APP_TOKEN).start()
