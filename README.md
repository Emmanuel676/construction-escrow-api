# Construction Escrow & Hardware API

FastAPI backend combining milestone-based construction escrow with a hardware e-commerce store.

## Overview

The API serves a construction marketplace piloting in Luweero, Uganda:

- **Milestone escrow** – an engineer and client agree on a milestone (e.g. a foundation) and its budget. The contract starts as `PENDING_PAYMENT` and becomes `ESCROW_LOCKED` once the client's mobile-money payment is confirmed.
- **Hardware store** – contractors order building materials for delivery to a site. Orders start as `AWAITING_FULFILLMENT` and become `PAID_PROCESSING` once paid.
- **Payments webhook** – a single mock Yo! Payments callback that settles both escrow locks and store purchases.
- **User profiles** – trust badges (mocked Laboremus identity / Verify.ug credential checks) and a link to the engineer's blueprint in Supabase Storage.

| Method | Path                               | Purpose                                    |
| ------ | ---------------------------------- | ------------------------------------------ |
| POST   | `/api/v1/contracts/create`         | Create a milestone escrow contract         |
| POST   | `/api/v1/store/order`              | Place a hardware order                     |
| POST   | `/api/v1/mock-payment/webhook`     | Payment provider callback                  |
| GET    | `/api/v1/users/profile/{id}`       | User profile, trust badges, blueprint URL  |
| GET    | `/api/v1/health`                   | Health check                               |

## Stack

- **Python 3.12**, **FastAPI**, **Pydantic v2** / pydantic-settings
- **SQLAlchemy 2.0** (typed `Mapped[...]` models) + **Alembic** migrations
- **SQLite** for local development, **Supabase PostgreSQL** in the cloud
- **Supabase Storage** for engineering blueprints (`supabase` Python client)
- **pytest** + FastAPI `TestClient` for tests

## Project structure

```
construction-escrow-api/
├── alembic/                    # Migration environment and versions
│   ├── env.py                  # Reads DATABASE_URL from app settings
│   └── versions/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/          # contracts, store, payments, users, health
│   │   └── router.py
│   ├── core/config.py          # Environment-based settings
│   ├── db/                     # Declarative Base and session / get_db
│   ├── models/                 # One file per ORM model + enums.py
│   ├── schemas/                # Pydantic request/response models
│   ├── services/               # Business logic (orders, payments, storage)
│   └── main.py                 # FastAPI app
├── scripts/seed.py             # Idempotent sample users
├── tests/
├── alembic.ini
├── requirements.txt
└── .env.example
```

## Setup

### PowerShell (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env

alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

### bash (macOS / Linux / Git Bash)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Git Bash on Windows: source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env

alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000. Edit `.env` to point `DATABASE_URL` at Supabase Postgres, add Supabase Storage credentials, or set `WEBHOOK_SECRET`. Never commit `.env`.

The seed script creates user **4** (Alex Mukasa, Civil Engineer, with blueprint `alex-mukasa/foundation-plan.pdf`) and user **12** (a sample contractor). It is safe to run repeatedly.

## Testing the API

### Interactive docs

Open http://127.0.0.1:8000/docs (Swagger UI) to try every endpoint from the browser.

### curl

All examples use the challenge brief's sample payloads. The brief's budget value appeared truncated ("35"), so `35000000` UGX (35 million) is used as the example milestone budget.

The examples below use bash syntax; see [PowerShell (Invoke-RestMethod)](#powershell-invoke-restmethod) for Windows equivalents.

**1. Create a milestone contract**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/contracts/create \
  -H "Content-Type: application/json" \
  -d '{
    "engineer_name": "John Doe",
    "client_name": "Luweero Property Developers Ltd",
    "project_location": "Luweero Town",
    "milestone_title": "Foundation Concrete Pour",
    "milestone_budget_ugx": 35000000
  }'
```

Returns `201` with the stored contract (`"status": "PENDING_PAYMENT"`). A location outside Luweero (e.g. `"Kampala"`) returns `422`.

**2. Place a hardware order**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/store/order \
  -H "Content-Type: application/json" \
  -d '{
    "contractor_id": 12,
    "delivery_site_location": "Wobulenzi, Luweero",
    "items": [
      {"product_id": 101, "product_name": "Tororo Cement Bag", "quantity": 50, "unit_price_ugx": 32000},
      {"product_id": 204, "product_name": "Electrical Conduit Pipe", "quantity": 15, "unit_price_ugx": 8500}
    ]
  }'
```

Returns `201` with the order, its items (line totals `1600000` and `127500`) and `"total_amount_ugx": 1727500`, all computed on the server. An unknown `contractor_id` returns `404`.

**3. Payment webhook**

Lock the escrow for contract 1:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/mock-payment/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: $WEBHOOK_SECRET" \
  -d '{
    "transaction_reference": "TXN-YO-112233",
    "payment_type": "ESCROW_LOCK",
    "reference_id": 1,
    "transaction_status": "SUCCESS"
  }'
```

Pay for hardware order 1:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/mock-payment/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: $WEBHOOK_SECRET" \
  -d '{
    "transaction_reference": "TXN-YO-112234",
    "payment_type": "STORE_PURCHASE",
    "reference_id": 1,
    "transaction_status": "SUCCESS"
  }'
```

The header is only checked when `WEBHOOK_SECRET` is set in `.env`; export the same value in your shell (`export WEBHOOK_SECRET=...`). Possible responses:

| Situation                                   | Response                                       |
| ------------------------------------------- | ---------------------------------------------- |
| Successful payment applied                  | `200` `{"detail": "payment applied", ...}`     |
| Same `transaction_reference` sent again     | `200` `{"detail": "duplicate callback ignored"}` |
| `transaction_status` other than `SUCCESS`   | `200`, recorded with `applied: false`          |
| Contract / order does not exist             | `404`                                          |
| Record already moved past its initial status| `409`                                          |
| Wrong or missing secret (when configured)   | `401`                                          |

**4. User profile**

```bash
curl http://127.0.0.1:8000/api/v1/users/profile/4
```

```json
{
  "user_id": 4,
  "name": "Alex Mukasa",
  "role": "Civil Engineer",
  "is_identity_verified_by_laboremus": true,
  "is_credentials_verified_by_verify_ug": true,
  "cloud_storage_blueprint_url": "https://<project-ref>.supabase.co/storage/v1/object/sign/blueprints/alex-mukasa/foundation-plan.pdf?token=..."
}
```

`cloud_storage_blueprint_url` is a signed URL when `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set, the bucket's public URL when only `SUPABASE_URL` is set (or signing fails), and `null` when Supabase is not configured. An unknown id returns `404`.

### PowerShell (Invoke-RestMethod)

```powershell
$base = "http://127.0.0.1:8000/api/v1"

# 1. Create a milestone contract
$contract = @{
    engineer_name        = "John Doe"
    client_name          = "Luweero Property Developers Ltd"
    project_location     = "Luweero Town"
    milestone_title      = "Foundation Concrete Pour"
    milestone_budget_ugx = 35000000
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/contracts/create" -ContentType "application/json" -Body $contract

# 2. Place a hardware order
$order = @{
    contractor_id          = 12
    delivery_site_location = "Wobulenzi, Luweero"
    items = @(
        @{ product_id = 101; product_name = "Tororo Cement Bag"; quantity = 50; unit_price_ugx = 32000 }
        @{ product_id = 204; product_name = "Electrical Conduit Pipe"; quantity = 15; unit_price_ugx = 8500 }
    )
} | ConvertTo-Json -Depth 3
Invoke-RestMethod -Method Post -Uri "$base/store/order" -ContentType "application/json" -Body $order

# 3. Payment webhook (escrow lock, then store purchase)
$headers = @{}
if ($env:WEBHOOK_SECRET) { $headers["X-Webhook-Secret"] = $env:WEBHOOK_SECRET }
$escrow = @{
    transaction_reference = "TXN-YO-112233"
    payment_type          = "ESCROW_LOCK"
    reference_id          = 1
    transaction_status    = "SUCCESS"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/mock-payment/webhook" -ContentType "application/json" -Headers $headers -Body $escrow

$purchase = @{
    transaction_reference = "TXN-YO-112234"
    payment_type          = "STORE_PURCHASE"
    reference_id          = 1
    transaction_status    = "SUCCESS"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/mock-payment/webhook" -ContentType "application/json" -Headers $headers -Body $purchase

# 4. User profile
Invoke-RestMethod -Uri "$base/users/profile/4"
```

Set `$env:WEBHOOK_SECRET` to the value in `.env` if you configured one.

### Automated tests

```bash
pytest
```

Tests run against a temporary SQLite database and never touch your local `escrow.db`.

## Design decisions

- **Case-insensitive Luweero check** – `project_location` is accepted when it contains "luweero" in any casing (`"Luweero Town"`, `"Wobulenzi, Luweero"`, `"LUWEERO"`), so users aren't rejected for capitalisation. Failures return `422` with a clear message.
- **Server-side totals** – the client sends quantities and unit prices only. The server computes each `line_total_ugx` and the order's `total_amount_ugx`, and saves the order and its items in one transaction. A client-supplied total is never trusted.
- **Integer UGX amounts** – money is stored as `BigInteger` shillings (UGX has no minor unit in practice), avoiding floating-point errors.
- **Idempotent webhook** – every callback is stored in `payment_transactions` with a unique `transaction_reference`. A repeated reference returns `200` without changing anything; the unique constraint also covers concurrent retries. Status changes happen only on `SUCCESS` and only from the record's initial status, otherwise `409`. Each callback is recorded with an `applied` flag for auditing.
- **Shared-secret check** – when `WEBHOOK_SECRET` is configured, `X-Webhook-Secret` is compared with `hmac.compare_digest` to avoid timing attacks.
- **Contracts store names as strings** – following the spec, `engineer_name` and `client_name` are plain strings rather than foreign keys. They can be linked to `users` later without breaking the API.
- **Users table added** – the spec references a `contractor_id` and user profiles, so a minimal `users` table backs both: orders have a real foreign key, and profiles hold the blueprint object key.
- **Layered structure** – routers handle HTTP, `app/services` hold business rules and raise domain errors (`NotFoundError`, `ConflictError`), which routers map to status codes.

## Architecture: why Supabase

- **Managed PostgreSQL and S3-compatible Storage on one platform** – the relational data (contracts, orders, payments) and the files (engineering blueprints) share one provider, one dashboard and one set of credentials. Moving from SQLite only means changing `DATABASE_URL`, and Alembic migrations run unchanged.
- **Signed URLs keep blueprints private** – blueprints sit in a private bucket. The API issues time-limited signed URLs (`SIGNED_URL_EXPIRY_SECONDS`) with the server-side service-role key, so drawings are never publicly listable and links expire.
- **Generous free tier** – a free Postgres database plus storage is enough for an early-stage startup to pilot in Luweero at no cost, and it scales with paid plans when traction comes.
- **Region choice for latency to Uganda** – projects can be created in the region closest to East African users (e.g. an EU or Middle East region) to reduce round-trip time for mobile users.
- **Easy path to deploy on Render** – the API is a standard ASGI app. On Render it runs with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, with `DATABASE_URL`, the Supabase keys and `WEBHOOK_SECRET` set as environment variables and `alembic upgrade head` as the pre-deploy command.
