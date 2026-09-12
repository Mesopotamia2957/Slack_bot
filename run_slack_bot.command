#!/bin/bash
cd "/Users/bbakjae/PycharmProjects/Slack_bot"
echo "=== Slack_bot 서버 시작 (JerryBot_V2가 먼저 떠 있어야 정상 동작) ==="
exec "/Users/bbakjae/PycharmProjects/Slack_bot/.venv/bin/python" slack_command.py
