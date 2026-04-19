from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel

class ChannelRead(ORMModel):
    id: UUID
    platform: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class MonitoringSourceRead(ORMModel):
    id: UUID
    platform: str
    source_url: str
    source_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ChannelCreate(BaseModel):
    platform: str
    name: str
    credentials: dict = Field(default_factory=dict)
    
class MonitoringSourceCreate(BaseModel):
    platform: str
    source_url: str
    source_type: str
