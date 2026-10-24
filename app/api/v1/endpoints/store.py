from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import HardwareOrder
from app.schemas.order import OrderCreate, OrderRead
from app.services import order_service
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/store", tags=["store"])


@router.post("/order", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)) -> HardwareOrder:
    try:
        return order_service.create_order(db, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)
