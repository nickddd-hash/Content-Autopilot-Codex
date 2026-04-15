from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_products: int
    active_products: int
    autopilot_enabled_products: int
    total_content_plans: int
    planned_items: int
    published_items: int
    failed_items: int
    running_jobs: int

