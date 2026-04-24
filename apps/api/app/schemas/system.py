from __future__ import annotations

from pydantic import BaseModel, Field


class SystemSettingRead(BaseModel):
    key: str
    value: str | None = None
    description: str | None = None


class SystemSettingsUpdatePayload(BaseModel):
    settings: list[SystemSettingRead] = Field(default_factory=list)
