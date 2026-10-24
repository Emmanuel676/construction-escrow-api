from fastapi import APIRouter

from app.api.v1.endpoints import contracts, health, payments, store

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(contracts.router)
api_router.include_router(store.router)
api_router.include_router(payments.router)
