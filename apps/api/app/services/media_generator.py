from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_plan import ContentPlanItem
from app.models.system import SystemSetting


async def generate_kie_video(db: AsyncSession, item: ContentPlanItem) -> str:
    """
    Mock implementation of Kie.ai video generation.
    In a real scenario, this would call the Kie.ai API using KIE_AI_API_KEY.
    """
    # Get API key
    setting = await db.scalar(select(SystemSetting).where(SystemSetting.key == "KIE_AI_API_KEY"))
    api_key = setting.value if setting else None
    
    if not api_key:
        print("Warning: KIE_AI_API_KEY not set. Running in mock mode.")
        
    # Simulate a generation delay and returning a video URL
    video_url = f"https://kie.ai/generated_video_{item.id}.mp4"
    
    # Update the item with the new media asset
    media_assets = dict(item.media_assets) if item.media_assets else {}
    if "videos" not in media_assets:
        media_assets["videos"] = []
    
    media_assets["videos"].append(video_url)
    item.media_assets = media_assets
    
    await db.commit()
    await db.refresh(item)
    
    return video_url
