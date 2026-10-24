from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models import User
from app.schemas.user import UserProfile
from app.services.storage import get_blueprint_url

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile/{user_id}", response_model=UserProfile)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserProfile:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )

    return UserProfile(
        user_id=user.id,
        name=user.name,
        role=user.role,
        # Mock trust badges: stand-ins for Laboremus (identity / KYC) and
        # Verify.ug (professional credentials) until those integrations exist.
        is_identity_verified_by_laboremus=True,
        is_credentials_verified_by_verify_ug=True,
        cloud_storage_blueprint_url=get_blueprint_url(
            user.blueprint_object_key, settings
        ),
    )
