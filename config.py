import os
from dotenv import load_dotenv

load_dotenv()

LOG_FILE = os.getenv('LOG_FILE')
DB_FILE = os.getenv('DB_FILE')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
LAST_PROCESSED_FILE = 'last_processed.json'