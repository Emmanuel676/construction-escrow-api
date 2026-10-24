from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User


@pytest.fixture
def db_session(tmp_path: Path) -> Generator[Session, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with TestingSession() as session:
        session.add_all(
            [
                User(
                    id=4,
                    name="Alex Mukasa",
                    role="Civil Engineer",
                    blueprint_object_key="alex-mukasa/foundation-plan.pdf",
                ),
                User(id=12, name="Sample Contractor (Demo)", role="Contractor"),
            ]
        )
        session.commit()
        yield session

    engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    # Isolate tests from the developer's .env / environment: no webhook secret,
    # no Supabase.
    test_settings = Settings(
        _env_file=None,
        SUPABASE_URL="",
        SUPABASE_SERVICE_ROLE_KEY="",
        WEBHOOK_SECRET="",
    )
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
