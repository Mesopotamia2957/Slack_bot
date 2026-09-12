FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TZ=Asia/Seoul
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Socket Mode 라 인바운드 포트 없음. 설정은 환경변수(BOT_TOKEN, APP_TOKEN, URI, API_KEY)로 받는다.
CMD ["python", "slack_command.py"]
