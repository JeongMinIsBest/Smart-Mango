# 설정값만 모아두는 파일

import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TEST_GUILD_ID = os.getenv("TEST_GUILD_ID")
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN이 .env에 설정되어 있지 않습니다.")

if TEST_GUILD_ID:
    TEST_GUILD_ID = int(TEST_GUILD_ID)
else:
    TEST_GUILD_ID = None

BOT_STATUS = "명령어 확인은 /도움말"

WORK_SECONDS = 25 * 60
SHORT_BREAK_SECONDS = 5 * 60
LONG_BREAK_SECONDS = 30 * 60