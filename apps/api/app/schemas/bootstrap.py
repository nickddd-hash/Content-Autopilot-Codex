from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class BootstrapWorkspaceResponse(BaseModel):
    product_id: UUID
    brand_profile_id: UUID
    content_plan_id: UUID
    product_created: bool
    brand_profile_created: bool
    content_plan_created: bool
    seeded_items_count: int
