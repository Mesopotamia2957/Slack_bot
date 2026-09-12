"""슬랙 메시지 포맷. 공고 제목 자체가 링크가 되도록 mrkdwn 을 쓴다."""

from . import config


def _line(posting):
    meta = posting.get('meta') or ''
    label = posting.get('meta_label') or ''
    suffix = f' _({label} {meta})_' if meta else ''
    return f'• <{posting["url"]}|{posting["title"]}>{suffix}'


def postings(results, total=None, header='', empty='조건에 맞는 공고가 없습니다.', group_by_company=False):
    if not results:
        return empty

    lines = [header] if header else []
    if group_by_company:
        current = None
        for posting in results[:config.MAX_ITEMS]:
            if posting['company'] != current:
                current = posting['company']
                lines.append(f'\n*🏢 {current}*')
            lines.append(_line(posting))
    else:
        lines.extend(_line(posting) for posting in results[:config.MAX_ITEMS])

    shown = min(len(results), config.MAX_ITEMS)
    if total and total > shown:
        lines.append(f'\n_… 외 {total - shown}건이 더 있습니다. 키워드로 좁혀보세요._')
    return '\n'.join(lines)


def companies(items):
    lines = ['*지원 중인 기업 목록*  (`!기업명` 으로 조회)']
    for item in items:
        count = item.get('open_count', 0)
        lines.append(f'• *{item["name"]}* — 진행 중 {count}건  <{item["career_url"]}|채용 페이지>')
    return '\n'.join(lines)


def keyword_list(keywords):
    if not keywords:
        return ('등록된 키워드가 없습니다.\n'
                '`!키워드추가 백엔드 django` 처럼 등록하면 새 공고를 DM으로 알려드려요.')
    joined = ', '.join(f'`{keyword}`' for keyword in keywords)
    return f'등록된 키워드: {joined}'


HELP = """*JerryBot 사용법*
채용공고를 모아두고, 관심 키워드에 맞는 새 공고가 올라오면 DM으로 알려드려요.

*처음이신가요?*
1️⃣ `!키워드추가 백엔드` — 관심 키워드를 등록하세요
2️⃣ 끝입니다. 새 공고가 올라오면 알아서 DM이 갑니다.

*공고 보기*
• `!목록` — 지원하는 기업과 진행 중 공고 수
• `!네이버` — 해당 기업의 진행 중 공고 (기업명을 그대로 쓰세요)
• `!검색 백엔드 django` — 모든 기업에서 키워드로 검색

*내 키워드*
• `!키워드` — 내 키워드 보기
• `!키워드추가 백엔드 서버` — 키워드 등록 (공백으로 여러 개)
• `!키워드삭제 백엔드` — 키워드 삭제
• `!내공고` — 내 키워드에 맞는 공고 전부 보기
• `!알림 끄기` / `!알림 켜기` — DM 알림 on/off

*알아두면 좋은 것*
• 키워드는 공고 제목과 직군에서 찾습니다. 대소문자는 구분하지 않아요.
• 여러 개 등록하면 그중 *하나라도* 맞는 공고를 알려드립니다.
• 한 번 알려드린 공고는 다시 보내지 않아요.
• 저에게 DM으로 말을 걸면 알림도 DM으로 갑니다. (공개 채널에서 등록해도 알림은 DM으로 가요)
"""

# `!` 없이 말을 걸었을 때 보여줄 짧은 안내
NUDGE = ('안녕하세요! 명령어는 `!` 로 시작해요.\n'
         '• `!키워드추가 백엔드` — 관심 키워드 등록하고 새 공고 DM 받기\n'
         '• `!목록` — 지원하는 기업 보기\n'
         '• `!도움말` — 전체 사용법')
