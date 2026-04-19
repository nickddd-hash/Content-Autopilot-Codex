import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monitoring import IngestedContent, MonitoringSource
from app.models.system import SystemSetting


async def run_apify_scraper(db: AsyncSession, source: MonitoringSource) -> list[IngestedContent]:
    """
    Mock implementation of Apify Scraper.
    In a real scenario, this would call the Apify API using APIFY_API_KEY.
    """
    # Get API key
    setting = await db.scalar(select(SystemSetting).where(SystemSetting.key == "APIFY_API_KEY"))
    api_key = setting.value if setting else None
    
    if not api_key:
        print("Warning: APIFY_API_KEY not set. Running in mock mode.")
        
    # Mocking scraper results
    mock_post = IngestedContent(
        source_id=source.id,
        external_id=str(uuid.uuid4()),
        platform=source.platform,
        content_type="video",
        text_content=f"Viral content from {source.source_url}",
        media_urls=["https://example.com/viral_video.mp4"],
        engagement_score=0.95,
        raw_data={"likes": 15000, "comments": 300},
        is_processed=False
    )
    
    db.add(mock_post)
    await db.commit()
    await db.refresh(mock_post)
    
    return [mock_post]
