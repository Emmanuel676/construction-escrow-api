"""Idempotently seed the sample users used by the API examples.

Run from the project root: python scripts/seed.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402

SEED_USERS: list[dict[str, int | str | None]] = [
    {
        "id": 4,
        "name": "Alex Mukasa",
        "role": "Civil Engineer",
        "blueprint_object_key": "alex-mukasa/foundation-plan.pdf",
    },
    {
        "id": 12,
        "name": "Sample Contractor (Demo)",
        "role": "Contractor",
        "blueprint_object_key": None,
    },
]


def seed() -> None:
    with SessionLocal() as db:
        for data in SEED_USERS:
            user = db.get(User, data["id"])
            if user is None:
                db.add(User(**data))
                print(f"Created user {data['id']}: {data['name']}")
            else:
                for field, value in data.items():
                    setattr(user, field, value)
                print(f"User {data['id']} already exists; ensured seed values")
        db.commit()


if __name__ == "__main__":
    seed()
