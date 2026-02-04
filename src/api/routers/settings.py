from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from api.deps import get_session
from core.domain.settings import Settings
from api.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=SettingsResponse)
def get_settings(session: Session = Depends(get_session)):
    settings = session.get(Settings, 1)
    if not settings:
        settings = Settings(id=1)
        session.add(settings)
        session.commit()
        session.refresh(settings)

    return settings.mask_api_keys()


@router.put("/", response_model=SettingsResponse)
def update_settings(
    settings_in: SettingsUpdate, session: Session = Depends(get_session)
):
    settings = session.get(Settings, 1)
    if not settings:
        settings = Settings(id=1)

    update_data = settings_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    settings.updated_at = datetime.now(timezone.utc)

    session.add(settings)
    session.commit()
    session.refresh(settings)

    return settings.mask_api_keys()
