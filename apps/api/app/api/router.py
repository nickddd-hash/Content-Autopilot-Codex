from fastapi import APIRouter

from app.api.routes import brand_profile, content_plans, dashboard, health, products, system_settings, telegram_auth


api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(brand_profile.router, prefix="/brand-profile", tags=["brand-profile"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(content_plans.router, prefix="/content-plans", tags=["content-plans"])
api_router.include_router(system_settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(telegram_auth.router, prefix="/telegram", tags=["telegram"])
