import os
from telethon import TelegramClient
from app.core.config import settings

SESSION_DIR = "/root/.gemini/tmp/root/sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

async def publish_with_userbot(chat_id: str | int, text: str, image_path: str = None):
    """
    Publishes a post using Telethon (Userbot).
    Supports long captions (up to 2048 for Premium, 1024 for others) 
    and long messages (up to 4096).
    """
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be configured.")

    session_path = os.path.join(SESSION_DIR, "userbot_session")
    
    async with TelegramClient(session_path, settings.telegram_api_id, settings.telegram_api_hash) as client:
        if image_path and os.path.exists(image_path):
            # For photos, Telethon automatically uses Premium limits if the account has Premium
            await client.send_file(
                chat_id, 
                image_path, 
                caption=text, 
                parse_mode='html'
            )
        else:
            await client.send_message(
                chat_id, 
                text, 
                parse_mode='html',
                link_preview=True
            )
