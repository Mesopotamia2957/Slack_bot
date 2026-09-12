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
    return {'X-API-Key': config.API_KEY} if config.API_KEY else {}


def _request(method, path, **kwargs):
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
    return _request('GET', 'companies/')


def company_postings(code, limit=None):
    params = {'limit': limit} if limit else {}
    return _request('GET', f'{code}/', params=params)


def search_postings(keywords, limit=None):
    params = {'keyword': ' '.join(keywords)}
    if limit:
        params['limit'] = limit
    return _request('GET', 'postings/', params=params)


def get_subscriber(user_id):
    return _request('GET', f'subscribers/{user_id}/')


def update_subscriber(user_id, **fields):
    return _request('POST', f'subscribers/{user_id}/', json=fields)


def get_keywords(user_id):
    return _request('GET', f'subscribers/{user_id}/keywords/')


def add_keywords(user_id, keywords, channel_id=''):
    return _request('POST', f'subscribers/{user_id}/keywords/',
                    json={'keywords': keywords, 'channel_id': channel_id})


def remove_keywords(user_id, keywords):
    return _request('DELETE', f'subscribers/{user_id}/keywords/', json={'keywords': keywords})


def my_matches(user_id, limit=None):
    params = {'limit': limit} if limit else {}
    return _request('GET', f'subscribers/{user_id}/matches/', params=params)
