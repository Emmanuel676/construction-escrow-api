import logging
from functools import lru_cache

from supabase import Client, create_client

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@lru_cache
def _get_client(url: str, key: str) -> Client:
    return create_client(url, key)


def _public_url(settings: Settings, object_key: str) -> str:
    base = settings.SUPABASE_URL.rstrip("/")
    return (
        f"{base}/storage/v1/object/public/"
        f"{settings.SUPABASE_STORAGE_BUCKET}/{object_key.lstrip('/')}"
    )


def get_blueprint_url(
    object_key: str | None, settings: Settings | None = None
) -> str | None:
    """Resolve a blueprint object key to a downloadable Supabase Storage URL.

    Prefers a time-limited signed URL (keeps blueprints private), falls back to
    the bucket's public URL, and returns None when storage is not configured.
    """
    settings = settings or get_settings()
    if not object_key or not settings.SUPABASE_URL:
        return None

    if settings.SUPABASE_SERVICE_ROLE_KEY:
        try:
            client = _get_client(
                settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
            )
            signed = client.storage.from_(
                settings.SUPABASE_STORAGE_BUCKET
            ).create_signed_url(object_key, settings.SIGNED_URL_EXPIRY_SECONDS)
            signed_url = signed.get("signedURL") or signed.get("signedUrl")
            if signed_url:
                return signed_url
        except Exception:
            logger.warning(
                "Failed to sign blueprint URL for %s; using public URL",
                object_key,
                exc_info=True,
            )

    return _public_url(settings, object_key)
