"""
Configuration file for Telegram Members Parser
Copy this file to config_local.py and fill in your credentials
"""

import os
from typing import Optional

def get_env_var(var_name: str, default: Optional[str] = None) -> str:
    """Get environment variable or return default value"""
    value = os.getenv(var_name, default)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set")
    return value

# Telegram API credentials
# Get these from https://my.telegram.org/apps
API_ID = get_env_var('TG_API_ID', 'YOUR_API_ID')
API_HASH = get_env_var('TG_API_HASH', 'YOUR_API_HASH')
PHONE_NUMBER = get_env_var('TG_PHONE_NUMBER', '+YOUR_PHONE_NUMBER')
GROUP_LINK = get_env_var('TG_GROUP_LINK', 'https://t.me/YOUR_CHANNEL')

# Optional: Session name for Telegram client
SESSION_NAME = get_env_var('TG_SESSION_NAME', 'session_name')
