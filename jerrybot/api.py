"""JerryBot_V2 API 클라이언트.

예전 봇은 타임아웃 없이 requests.get 을 호출해서, 서버가 크롤링에 묶이면
슬랙 핸들러가 무한정 대기했다. 여기서는 모든 요청에 타임아웃을 건다.
"""

import logging

import requests

from . import config

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """사용자에게 그대로 보여줄 수 있는 오류 메시지를 담는다."""


class NotFoundError(ApiError):
    """없는 기업을 물어봤을 때처럼, 호출한 쪽에서 안내를 다르게 하고 싶은 경우."""


def _headers():
    """API 키가 설정돼 있을 때만 X-API-Key 를 붙인다.

    서버(JERRYBOT_API_KEY)와 봇(API_KEY)이 같은 값일 때만 인증이 성립한다.
    둘 다 비어 있으면 인증 없이 열린 상태로 동작한다 — 내부망 전용이라 가능한 구성이다.
    """
    return {'X-API-Key': config.API_KEY} if config.API_KEY else {}


def _request(method, path, **kwargs):
    """모든 API 호출이 거쳐 가는 자리. 네트워크 오류와 HTTP 오류를 사용자용 한국어 메시지로 바꾼다.

    여기서 예외를 ApiError 로 통일하는 이유는, 핸들러가 오류마다 다른 처리를 하지 않고
    '메시지를 그대로 슬랙에 보내면 되는 것' 하나로 다룰 수 있게 하기 위해서다.
    타임아웃을 반드시 거는 것도 중요하다 — 서버가 크롤링에 묶이면 봇 전체가 멈춘다.
    """
    url = config.BASE_URL + path.lstrip('/')
    try:
        response = requests.request(
            method, url, timeout=config.REQUEST_TIMEOUT, headers=_headers(), **kwargs
        )
    except requests.Timeout:
        raise ApiError('서버 응답이 너무 느립니다. 잠시 후 다시 시도해 주세요.')
    except requests.ConnectionError:
        raise ApiError('공고 서버에 연결할 수 없습니다. 관리자에게 문의해 주세요.')

    if response.status_code == 404:
        raise NotFoundError('요청하신 대상을 찾을 수 없습니다.')
    if response.status_code == 401:
        raise ApiError('API 인증에 실패했습니다. 관리자에게 문의해 주세요.')
    if not response.ok:
        logger.error('API 오류 %s %s -> %s', method, url, response.status_code)
        raise ApiError(f'서버 오류가 발생했습니다. (코드 {response.status_code})')

    try:
        return response.json()
    except ValueError:
        raise ApiError('서버 응답을 이해할 수 없습니다.')


def list_companies():
    """크롤링 대상 기업과 각 기업의 진행 중 공고 수. `!목록` 이 쓴다."""
    return _request('GET', 'companies/')


def company_postings(code, limit=None):
    """기업 하나의 진행 중 공고. `!네이버` 처럼 기업명을 그대로 친 경우."""
    params = {'limit': limit} if limit else {}
    return _request('GET', f'{code}/', params=params)


def search_postings(keywords, limit=None):
    """모든 기업에서 키워드로 검색. `!검색 백엔드 django`.

    키워드를 공백으로 이어 붙여 보낸다 — 서버가 쉼표·공백을 모두 구분자로 받는다.
    """
    params = {'keyword': ' '.join(keywords)}
    if limit:
        params['limit'] = limit
    return _request('GET', 'postings/', params=params)


def get_subscriber(user_id):
    """내 구독 정보(키워드·알림 상태). 없으면 서버가 만들어서 돌려준다."""
    return _request('GET', f'subscribers/{user_id}/')


def update_subscriber(user_id, **fields):
    """알림 on/off, 표시 이름, 알림 받을 대화방을 갱신한다."""
    return _request('POST', f'subscribers/{user_id}/', json=fields)


def get_keywords(user_id):
    """내 키워드 목록. `!키워드`."""
    return _request('GET', f'subscribers/{user_id}/keywords/')


def add_keywords(user_id, keywords, channel_id=''):
    """키워드를 등록한다. `!키워드추가 백엔드 서버`.

    channel_id 를 같이 보내는 이유는, DM 에서 등록했다면 그 대화방을 알림 채널로
    기억해 두기 위해서다(공개 채널이면 핸들러가 빈 값으로 보낸다).
    """
    return _request('POST', f'subscribers/{user_id}/keywords/',
                    json={'keywords': keywords, 'channel_id': channel_id})


def remove_keywords(user_id, keywords):
    """키워드를 지운다. `!키워드삭제 백엔드`."""
    return _request('DELETE', f'subscribers/{user_id}/keywords/', json={'keywords': keywords})


def save_inbox(text):
    """옵시디언 인박스에 메모 한 건을 남긴다. inbox-api 가 파일을 만들고 git 은 서버가 알아서 올린다."""
    if not config.INBOX_URL:
        raise ApiError('메모 저장이 설정되지 않았습니다. (INBOX_URL 없음)')
    try:
        response = requests.post(config.INBOX_URL, json={'text': text, 'source': 'slack'},
                                 timeout=config.REQUEST_TIMEOUT)
    except requests.RequestException:
        raise ApiError('메모 서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.')
    if not response.ok:
        raise ApiError(f'메모 저장에 실패했습니다. (코드 {response.status_code})')
    return response.json()


def my_matches(user_id, limit=None):
    """내 키워드에 맞는 공고 전부. 이미 알림받은 것도 포함한다. `!내공고`."""
    params = {'limit': limit} if limit else {}
    return _request('GET', f'subscribers/{user_id}/matches/', params=params)
