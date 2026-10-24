from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: int
    name: str
    role: str
    is_identity_verified_by_laboremus: bool
    is_credentials_verified_by_verify_ug: bool
    cloud_storage_blueprint_url: str | None
