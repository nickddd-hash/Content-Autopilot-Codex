from uuid import UUID
from pydantic import BaseModel, Field

class SystemSettingBase(BaseModel):
    key: str = Field(..., max_length=100)
    value: str | None = None
    description: str | None = Field(None, max_length=255)

class SystemSettingCreate(SystemSettingBase):
    pass

class SystemSettingUpdate(BaseModel):
    value: str | None = None
    description: str | None = Field(None, max_length=255)

class SystemSettingResponse(SystemSettingBase):
    id: UUID
    
    class Config:
        from_attributes = True

class SystemSettingsBulkUpdate(BaseModel):
    settings: dict[str, str | None]
