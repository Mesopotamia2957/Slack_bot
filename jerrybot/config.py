import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트의 .env 를 명시적으로 읽는다.
# 그냥 load_dotenv() 를 쓰면 실행한 위치(cwd)를 기준으로 찾기 때문에,
# 다른 디렉터리에서 봇을 띄우면 설정을 못 찾고 ConfigError 로 죽는다.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


class ConfigError(RuntimeError):
    pass


def _required(name):
    value = os.getenv(name, '').strip()
    if not value:
        raise ConfigError(f'.env 에 {name} 이(가) 없습니다. .env.example 을 참고하세요.')
    return value


BOT_TOKEN = _required('BOT_TOKEN')
APP_TOKEN = _required('APP_TOKEN')

# JerryBot_V2 API 주소. 예: http://localhost:8000/api/
BASE_URL = _required('URI').rstrip('/') + '/'

# 서버에 JERRYBOT_API_KEY 를 설정했다면 같은 값을 넣는다.
API_KEY = os.getenv('API_KEY', '').strip()

REQUEST_TIMEOUT = float(os.getenv('REQUEST_TIMEOUT', '10'))

# 옵시디언 인박스 작성기(inbox-api) 주소. 비워두면 `!메모` 가 안내만 한다.
INBOX_URL = os.getenv('INBOX_URL', '').strip()

# 한 메시지에 넣을 공고 수. 슬랙 메시지 길이 제한(약 4000자)을 넘지 않게 한다.
MAX_ITEMS = int(os.getenv('MAX_ITEMS', '25'))
