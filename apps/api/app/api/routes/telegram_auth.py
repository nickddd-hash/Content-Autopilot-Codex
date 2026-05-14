from __future__ import annotations

import json
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from app.core.config import settings

router = APIRouter()


def _session_path() -> str:
    os.makedirs(settings.telegram_session_dir, exist_ok=True)
    return os.path.join(settings.telegram_session_dir, "userbot_session")


def _hash_file() -> str:
    return os.path.join(settings.telegram_session_dir, "_auth_hash.json")


def _require_credentials() -> None:
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        raise HTTPException(status_code=400, detail="TELEGRAM_API_ID and TELEGRAM_API_HASH not configured.")


class SendCodeBody(BaseModel):
    phone: str | None = None


class SignInBody(BaseModel):
    code: str
    password: str | None = None


@router.get("/status")
async def auth_status() -> dict:
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        return {"configured": False, "authenticated": False}

    session_file = _session_path() + ".session"
    if not os.path.exists(session_file):
        return {"configured": True, "authenticated": False}

    client = TelegramClient(_session_path(), settings.telegram_api_id, settings.telegram_api_hash)
    try:
        await client.connect()
        authenticated = await client.is_user_authorized()
        return {"configured": True, "authenticated": authenticated}
    finally:
        await client.disconnect()


@router.post("/send-code")
async def send_code(body: SendCodeBody | None = None) -> dict:
    _require_credentials()
    phone = (body.phone if body and body.phone else None) or settings.telegram_phone
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number not provided and TELEGRAM_PHONE not configured.")

    client = TelegramClient(_session_path(), settings.telegram_api_id, settings.telegram_api_hash)
    try:
        await client.connect()
        result = await client.send_code_request(phone)
        with open(_hash_file(), "w") as f:
            json.dump({"phone": phone, "phone_code_hash": result.phone_code_hash}, f)
        return {"sent": True, "phone": phone}
    finally:
        await client.disconnect()


@router.post("/sign-in")
async def sign_in(body: SignInBody) -> dict:
    _require_credentials()

    hash_file = _hash_file()
    if not os.path.exists(hash_file):
        raise HTTPException(status_code=400, detail="No pending auth. Call /send-code first.")

    with open(hash_file) as f:
        data = json.load(f)

    phone = data["phone"]
    phone_code_hash = data["phone_code_hash"]

    client = TelegramClient(_session_path(), settings.telegram_api_id, settings.telegram_api_hash)
    try:
        await client.connect()
        try:
            await client.sign_in(phone, body.code, phone_code_hash=phone_code_hash)
        except SessionPasswordNeededError:
            if not body.password:
                raise HTTPException(status_code=400, detail="2FA password required. Pass it in the 'password' field.")
            await client.sign_in(password=body.password)

        os.remove(hash_file)
        return {"success": True}
    finally:
        await client.disconnect()
