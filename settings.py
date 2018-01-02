import os

# Telegram configuration settings

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
TELEGRAM_ADMINS_LIST = list(
    map(int, os.getenv('TELEGRAM_ADMINS_LIST').split(',')))
