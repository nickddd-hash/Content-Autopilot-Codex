from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.bootstrap import BootstrapWorkspaceResponse
from app.services.bootstrap import bootstrap_first_workspace


router = APIRouter()


@router.post("/bootstrap-first-workspace", response_model=BootstrapWorkspaceResponse)
async def bootstrap_workspace(
    session: AsyncSession = Depends(get_db_session),
) -> BootstrapWorkspaceResponse:
    return await bootstrap_first_workspace(session)
