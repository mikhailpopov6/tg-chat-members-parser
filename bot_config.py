"""
Bot Configuration
Configuration file for Telegram bot
"""

import os

# Bot Token - Get from @BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Bot settings
BOT_NAME = "Channel Members Parser Bot"
BOT_DESCRIPTION = "Парсер участников Telegram каналов с красивым выводом"
BOT_VERSION = "2.0"

# Parsing settings
MAX_PARTICIPANTS = 10000  # Maximum participants to parse
PARSING_DELAY = 0.5  # Delay between requests (seconds)
PROGRESS_UPDATE_INTERVAL = 5  # Update progress every N patterns

# File settings
EXCEL_FILENAME_PREFIX = "channel_members"
MAX_FILENAME_LENGTH = 50

# Logging settings
LOG_LEVEL = "INFO"
LOG_FILE = "telegram_bot.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Security settings
ALLOWED_USERS = []  # Empty list means all users allowed
ADMIN_USERS = []  # List of admin user IDs
MAX_REQUESTS_PER_HOUR = 10  # Rate limiting

# Export settings
EXCEL_COLUMNS = [
    'ID',
    'Username', 
    'Имя',
    'Фамилия',
    'Телефон',
    'Бот',
    'Верифицирован',
    'Premium'
]

# Emoji settings
EMOJIS = {
    'bot': '🤖',
    'user': '👤',
    'verified': '✅',
    'premium': '⭐',
    'phone': '📱',
    'channel': '📢',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'loading': '🔄',
    'search': '🔍',
    'file': '📁',
    'stats': '📊'
}
