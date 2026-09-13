"""슬랙 명령 처리.

예전에는 기업마다 @app.message 데코레이터를 하나씩 달았기 때문에
기업을 추가할 때마다 봇 코드도 같이 고쳐야 했다. 지금은 '!' 로 시작하는
메시지를 하나의 핸들러가 받아 서버에 물어보므로, 기업 추가는 서버 쪽
sites.py 만 고치면 된다.
"""

import logging
import re

from . import api, formatting

logger = logging.getLogger(__name__)

COMMAND_PATTERN = re.compile(r'^\s*!\s*(?P<command>\S*)\s*(?P<args>.*)$', re.DOTALL)

# `!` 없이 도움을 청하는 말들. DM 에서만 반응한다.
HELP_WORDS = {'도움말', '도움', '사용법', 'help', '?', '헬프', '명령어'}


def _args(raw):
    return [token for token in raw.replace(',', ' ').split() if token]


def _is_dm(channel_id):
    """DM 채널에서 온 메시지인지. 공개 채널 ID를 알림 채널로 저장하면
    개인 알림이 채널에 공개되므로 DM 일 때만 저장한다."""
    return bool(channel_id) and channel_id.startswith('D')


# ---------------------------------------------------------------------------
# 개별 명령
# ---------------------------------------------------------------------------

def cmd_help(**_):
    return formatting.HELP


def cmd_companies(**_):
    return formatting.companies(api.list_companies())


def cmd_search(args, **_):
    keywords = _args(args)
    if not keywords:
        return '검색어를 입력해 주세요. 예: `!검색 백엔드 django`'
    payload = api.search_postings(keywords)
    header = f'*"{" ".join(keywords)}" 검색 결과 {payload["count"]}건*'
    return formatting.postings(
        payload['results'], total=payload['count'], header=header,
        empty=f'"{" ".join(keywords)}" 에 맞는 공고가 없습니다.', group_by_company=True,
    )


def cmd_keywords(user_id, **_):
    return formatting.keyword_list(api.get_keywords(user_id)['keywords'])


def cmd_keyword_add(args, user_id, channel_id, **_):
    keywords = _args(args)
    if not keywords:
        return '추가할 키워드를 입력해 주세요. 예: `!키워드추가 백엔드 django`'

    payload = api.add_keywords(user_id, keywords, channel_id=channel_id if _is_dm(channel_id) else '')
    lines = []
    if payload['added']:
        lines.append('✅ 추가: ' + ', '.join(f'`{keyword}`' for keyword in payload['added']))
    if payload['already']:
        lines.append('이미 등록됨: ' + ', '.join(f'`{keyword}`' for keyword in payload['already']))
    lines.append(formatting.keyword_list(payload['keywords']))
    if payload['added']:
        lines.append('_새 공고가 올라오면 DM으로 알려드릴게요._')
    return '\n'.join(lines)


def cmd_keyword_remove(args, user_id, **_):
    keywords = _args(args)
    if not keywords:
        return '삭제할 키워드를 입력해 주세요. 예: `!키워드삭제 백엔드`'

    payload = api.remove_keywords(user_id, keywords)
    if not payload['removed']:
        return f'등록되지 않은 키워드입니다.\n{formatting.keyword_list(payload["keywords"])}'
    removed = ', '.join(f'`{keyword}`' for keyword in payload['removed'])
    return f'🗑 삭제: {removed}\n{formatting.keyword_list(payload["keywords"])}'


def cmd_my_postings(user_id, **_):
    payload = api.my_matches(user_id)
    if not payload['keywords']:
        return formatting.keyword_list([])
    header = f'*내 키워드({", ".join(payload["keywords"])})에 맞는 공고 {payload["count"]}건*'
    return formatting.postings(
        payload['results'], total=payload['count'], header=header,
        empty='아직 키워드에 맞는 공고가 없습니다. 새로 올라오면 알려드릴게요.',
        group_by_company=True,
    )


ON_WORDS = {'켜기', 'on', '켬', '시작'}
OFF_WORDS = {'끄기', 'off', '끔', '중지', '해제'}


def cmd_notify(args, user_id, channel_id, **_):
    tokens = _args(args)
    if not tokens or tokens[0].lower() not in ON_WORDS | OFF_WORDS:
        current = api.get_subscriber(user_id)['notify_enabled']
        state = '켜져' if current else '꺼져'
        return f'DM 알림이 {state} 있습니다. `!알림 켜기` 또는 `!알림 끄기` 로 바꿀 수 있어요.'

    enabled = tokens[0].lower() in ON_WORDS
    payload = api.update_subscriber(
        user_id, notify_enabled=enabled,
        channel_id=channel_id if _is_dm(channel_id) else '',
    )
    if payload['notify_enabled']:
        return '🔔 DM 알림을 켰습니다.\n' + formatting.keyword_list(payload['keywords'])
    return '🔕 DM 알림을 껐습니다. `!알림 켜기` 로 다시 받을 수 있어요.'


def cmd_company(command, **_):
    """등록된 기업명이면 공고를, 아니면 안내를 돌려준다."""
    try:
        payload = api.company_postings(command)
    except api.NotFoundError:
        return (f'`{command}` 는 등록되지 않은 명령이거나 기업입니다.\n'
                '`!목록` 으로 기업을 확인하거나 `!도움말` 을 입력해 보세요.')

    header = f'*🏢 {payload["company"]}* — 진행 중 {payload["count"]}건  <{payload["url"]}|채용 페이지>'
    return formatting.postings(
        payload['results'], total=payload['count'], header=header,
        empty=f'{payload["company"]} 에 현재 진행 중인 공고가 없습니다.',
    )


def cmd_memo(args, **_):
    """`!메모 내용` — 옵시디언 인박스에 남긴다. 줄바꿈도 그대로 들어간다."""
    text = (args or '').strip()
    if not text:
        return '남길 내용을 적어 주세요. 예: `!메모 다음 주 월요일 치과 예약`'
    payload = api.save_inbox(text)
    return (f'📥 인박스에 저장했어요 · `{payload["file"]}` ({payload["chars"]}자)\n'
            '_새벽 배치가 Daily 노트로 정리합니다._')


COMMANDS = {
    '메모': cmd_memo, '기록': cmd_memo, '인박스': cmd_memo, 'memo': cmd_memo,
    '도움말': cmd_help, 'help': cmd_help, '사용법': cmd_help,
    '목록': cmd_companies, '기업': cmd_companies, '기업목록': cmd_companies,
    '검색': cmd_search,
    '키워드': cmd_keywords, '내키워드': cmd_keywords,
    '키워드추가': cmd_keyword_add, '키워드등록': cmd_keyword_add,
    '키워드삭제': cmd_keyword_remove, '키워드제거': cmd_keyword_remove,
    '내공고': cmd_my_postings, '내알림': cmd_my_postings,
    '알림': cmd_notify,
}


def dispatch(text, user_id, channel_id):
    """'!' 로 시작하는 메시지 한 줄을 처리해 보낼 문자열을 돌려준다."""
    match = COMMAND_PATTERN.match(text or '')
    if not match:
        return None

    command = match.group('command')
    args = match.group('args')
    if not command:
        # `!` 만 입력한 경우
        return formatting.HELP
    handler = COMMANDS.get(command.lower(), cmd_company)

    try:
        return handler(command=command, args=args, user_id=user_id, channel_id=channel_id)
    except api.ApiError as exc:
        return f'⚠️ {exc}'
    except Exception:
        # 예상 못 한 오류로 봇이 조용히 죽지 않도록 로그를 남기고 안내만 보낸다.
        logger.exception('명령 처리 실패: %s', text)
        return '⚠️ 처리 중 오류가 발생했습니다. 관리자에게 문의해 주세요.'


def nudge(text, channel_id):
    """`!` 없이 말을 건 경우의 안내. DM 에서만 반응해 채널을 시끄럽게 하지 않는다."""
    if not _is_dm(channel_id):
        return None
    stripped = (text or '').strip().lower().rstrip('!?。.')
    if stripped in HELP_WORDS:
        return formatting.HELP
    return formatting.NUDGE if stripped else None


def register(app):
    @app.message(re.compile(r'^\s*!'))
    def handle_command(message, say):
        reply = dispatch(message.get('text', ''), message.get('user', ''), message.get('channel', ''))
        if reply:
            say(reply)

    @app.event('app_mention')
    def handle_mention(event, say):
        """@봇 을 멘션한 경우. 멘션 부분을 떼고 명령으로 처리한다."""
        text = re.sub(r'<@[A-Z0-9]+>', '', event.get('text', '')).strip()
        reply = dispatch(text, event.get('user', ''), event.get('channel', ''))
        say(reply or formatting.HELP)

    @app.event('message')
    def handle_plain_message(event, say):
        """DM 에서 `!` 없이 말을 건 경우에만 짧게 안내한다."""
        if event.get('bot_id') or event.get('subtype'):
            return
        text = event.get('text', '')
        if text.strip().startswith('!'):
            return  # 위 핸들러가 이미 처리했다
        reply = nudge(text, event.get('channel', ''))
        if reply:
            say(reply)
