"""슬랙봇 명령 처리 테스트. 서버도 슬랙도 없이 돈다.

    python -m unittest discover tests
"""

import unittest
from unittest.mock import patch

from jerrybot import api, formatting, handlers


def call(text, user_id='U1', channel_id='D1'):
    return handlers.dispatch(text, user_id, channel_id)


class DispatchTests(unittest.TestCase):
    def test_ignores_message_without_prefix(self):
        self.assertIsNone(call('그냥 잡담'))

    def test_bare_bang_shows_help(self):
        self.assertEqual(call('!'), formatting.HELP)

    def test_help_command(self):
        self.assertEqual(call('!도움말'), formatting.HELP)

    def test_help_aliases(self):
        for text in ['!help', '!사용법', '!HELP']:
            self.assertEqual(call(text), formatting.HELP, text)

    def test_leading_space_is_tolerated(self):
        self.assertEqual(call('  !도움말  '), formatting.HELP)

    def test_help_mentions_keyword_command(self):
        """온보딩의 핵심이므로 도움말에 반드시 들어 있어야 한다."""
        self.assertIn('!키워드추가', formatting.HELP)
        self.assertIn('!목록', formatting.HELP)


class KeywordCommandTests(unittest.TestCase):
    def test_add_keywords(self):
        payload = {'added': ['백엔드'], 'already': [], 'keywords': ['백엔드']}
        with patch.object(api, 'add_keywords', return_value=payload) as mock:
            reply = call('!키워드추가 백엔드')
        mock.assert_called_once()
        self.assertIn('백엔드', reply)
        self.assertIn('DM', reply)

    def test_add_multiple_keywords_split_on_space_and_comma(self):
        payload = {'added': ['백엔드', 'django'], 'already': [], 'keywords': ['django', '백엔드']}
        with patch.object(api, 'add_keywords', return_value=payload) as mock:
            call('!키워드추가 백엔드, django')
        self.assertEqual(mock.call_args[0][1], ['백엔드', 'django'])

    def test_add_without_argument_explains_usage(self):
        reply = call('!키워드추가')
        self.assertIn('키워드를 입력', reply)

    def test_remove_keyword(self):
        payload = {'removed': ['백엔드'], 'keywords': []}
        with patch.object(api, 'remove_keywords', return_value=payload):
            self.assertIn('백엔드', call('!키워드삭제 백엔드'))

    def test_list_keywords_when_empty_guides_user(self):
        with patch.object(api, 'get_keywords', return_value={'keywords': []}):
            reply = call('!키워드')
        self.assertIn('!키워드추가', reply)

    def test_notify_toggle(self):
        payload = {'notify_enabled': False, 'keywords': ['백엔드']}
        with patch.object(api, 'update_subscriber', return_value=payload):
            self.assertIn('껐', call('!알림 끄기'))


class CompanyCommandTests(unittest.TestCase):
    def test_unknown_command_falls_back_to_company_lookup(self):
        payload = {'company': '네이버', 'url': 'https://ex.com', 'count': 1,
                   'results': [{'title': '백엔드 개발자', 'url': 'https://ex.com/1',
                                'meta': '상시', 'meta_label': '마감'}]}
        with patch.object(api, 'company_postings', return_value=payload) as mock:
            reply = call('!네이버')
        mock.assert_called_once_with('네이버')
        self.assertIn('<https://ex.com/1|백엔드 개발자>', reply)

    def test_unknown_company_suggests_help(self):
        with patch.object(api, 'company_postings', side_effect=api.NotFoundError('없음')):
            reply = call('!없는회사')
        self.assertIn('!목록', reply)
        self.assertIn('!도움말', reply)


class ErrorHandlingTests(unittest.TestCase):
    def test_api_error_is_shown_to_user(self):
        with patch.object(api, 'list_companies', side_effect=api.ApiError('서버가 응답하지 않습니다.')):
            reply = call('!목록')
        self.assertIn('서버가 응답하지 않습니다.', reply)

    def test_unexpected_error_does_not_crash(self):
        with patch.object(api, 'list_companies', side_effect=ValueError('예상 못 한 오류')):
            reply = call('!목록')
        self.assertIn('오류', reply)
        self.assertNotIn('예상 못 한 오류', reply)  # 내부 오류 문구를 그대로 노출하지 않는다


class NudgeTests(unittest.TestCase):
    def test_dm_without_prefix_gets_hint(self):
        self.assertEqual(handlers.nudge('안녕하세요', 'D1'), formatting.NUDGE)

    def test_public_channel_is_silent(self):
        """공개 채널에서 아무 말에나 끼어들면 시끄럽다."""
        self.assertIsNone(handlers.nudge('안녕하세요', 'C1'))

    def test_help_word_without_prefix_shows_full_help(self):
        for text in ['도움말', 'help', '사용법', '명령어']:
            self.assertEqual(handlers.nudge(text, 'D1'), formatting.HELP, text)

    def test_empty_message_is_ignored(self):
        self.assertIsNone(handlers.nudge('   ', 'D1'))


class ConfigTests(unittest.TestCase):
    def test_env_is_found_from_any_working_directory(self):
        """다른 디렉터리에서 봇을 띄워도 .env 를 찾아야 한다.

        load_dotenv() 를 인자 없이 쓰면 실행 위치를 기준으로 찾기 때문에
        `python /경로/slack_command.py` 처럼 밖에서 실행하면 ConfigError 로 죽었다.
        """
        import subprocess
        import sys
        from pathlib import Path

        project = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, '-c',
             f'import sys; sys.path.insert(0, {str(project)!r});'
             ' from jerrybot import config; print(bool(config.BOT_TOKEN), bool(config.BASE_URL))'],
            cwd='/', capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('True True', result.stdout)


class RegistrationTests(unittest.TestCase):
    def test_listeners_register_without_conflict(self):
        """app.message 와 app.event('message') 를 함께 등록해도 문제가 없어야 한다."""
        from slack_bolt import App

        app = App(token='xoxb-test', signing_secret='test',
                  token_verification_enabled=False, request_verification_enabled=False)
        handlers.register(app)
        self.assertGreaterEqual(len(app._listeners), 3)


if __name__ == '__main__':
    unittest.main()
