import logging
import os

import certifi
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from jerrybot import config, handlers

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')

os.environ['SSL_CERT_FILE'] = certifi.where()

app = App(token=config.BOT_TOKEN)
handlers.register(app)


if __name__ == '__main__':
    SocketModeHandler(app, config.APP_TOKEN).start()
