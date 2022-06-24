import os
import dotenv

if os.path.isfile("variables.env"):
    dotenv.load_dotenv("variables.env")

# Environment variables
PHOTOS_WEBHOOK = str(os.environ.get("PHOTOS_WEBHOOK"))
ANIMATIONS_WEBHOOK = str(os.environ.get("ANIMATIONS_WEBHOOK"))
VIDEOS_WEBHOOK = str(os.environ.get("VIDEOS_WEBHOOK"))
AUDIO_WEBHOOK = str(os.environ.get("AUDIO_WEBHOOK"))
DOCUMENTS_WEBHOOK = str(os.environ.get("DOCUMENTS_WEBHOOK"))
MESSAGES_WEBHOOK = str(os.environ.get("MESSAGES_WEBHOOK"))
GROUP_WEBHOOK = str(os.environ.get("GROUP_WEBHOOK"))
FAILED_WEBHOOK = str(os.environ.get("FAILED_WEBHOOK"))
REDDIT_USER_AGENT = str(os.environ.get("REDDIT_USER_AGENT"))
REDDIT_CLIENT_ID = str(os.environ.get("REDDIT_CLIENT_ID"))
REDDIT_CLIENT_SECRET = str(os.environ.get("REDDIT_CLIENT_SECRET"))
REDDIT_USERNAME = str(os.environ.get("REDDIT_USERNAME"))
REDDIT_PASSWORD = str(os.environ.get("REDDIT_PASSWORD"))
TELEGRAM_BOT_TOKEN = str(os.environ.get("TELEGRAM_BOT_TOKEN"))
TELEGRAM_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID"))
SLEEP_BETWEEN_POSTS = int(os.environ.get("SLEEP_BETWEEN_POSTS"))
IDLE_SLEEP = int(os.environ.get("IDLE_SLEEP"))
SLEEP_ON_FAILED_GET = int(os.environ.get("SLEEP_ON_FAILED_GET"))
GET_ATTEMPTS = int(os.environ.get("GET_ATTEMPTS"))
SLEEP_ON_FAILED_POST = int(os.environ.get("SLEEP_ON_FAILED_POST"))
POST_ATTEMPTS = int(os.environ.get("POST_ATTEMPTS"))
REFRESH_AFTER_POSTS = int(os.environ.get("REFRESH_AFTER_POSTS"))

# Global constants
TEN_MB = int(10*1024*1024)
FIFTY_MB = int(50*1024*1024)
REQUEST_HEADERS = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36"
}