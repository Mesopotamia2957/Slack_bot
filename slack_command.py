from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import certifi
import os
import requests

load_dotenv()  # 환경 변수 파일을 로드
BOT_TOKEN = os.getenv('BOT_TOKEN')
APP_TOKEN = os.getenv('APP_TOKEN')
URI = os.getenv('URI')

os.environ['SSL_CERT_FILE'] = certifi.where()
# Initializes your app with your bot token and socket mode handler
app = App(token=BOT_TOKEN)
BASE_URL = URI


def slack_say(endpoint, message, say):
    url = BASE_URL + endpoint
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()
        data = results['url']
        for result in results['data']:
            data += ("\n------------------------------\n{0}\n[{1}]".format(result['name'], result['period']))
        say(data)
    else:
        print("Error:", response.status_code)
        say("Error: 크롤링 실패, 관리자에게 문의하세요")


@app.message("!네이버")
def message_hello(message, say):
    slack_say('naver', message, say)

@app.message("!카카오")
def message_hello(message, say):
    slack_say('kakao', message, say)

@app.message("!HL클레무브")
def message_hello(message, say):
    slack_say('hl_klemove', message, say)

@app.message("!hl클레무브")
def message_hello(message, say):
    slack_say('hl_klemove', message, say)

@app.message("!스노우")
def message_hello(message, say):
    slack_say('snow', message, say)

@app.message("!여기어때")
def message_hello(message, say):
    slack_say('gcccompany', message, say)

@app.message("!무신사")
def message_hello(message, say):
    slack_say('musinsa', message, say)

@app.message("!플렉스")
def message_hello(message, say):
    slack_say('flex', message, say)

@app.message("!넥슨")
def message_hello(message, say):
    slack_say('nexon', message, say)

@app.message("!두들린")
def message_hello(message, say):
    slack_say('doodlin', message, say)

@app.message("!SSG")
def message_hello(message, say):
    slack_say('ssg', message, say)

# @app.message("!신세계아이엔씨")
# def message_hello(message, say):
#     slack_say('shinsegaeinc', message, say)

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, APP_TOKEN).start()



