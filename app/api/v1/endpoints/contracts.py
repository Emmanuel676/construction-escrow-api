from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Contract
from app.models.enums import ContractStatus
from app.schemas.contract import ContractCreate, ContractRead

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post(
    "/create", response_model=ContractRead, status_code=status.HTTP_201_CREATED
)
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)) -> Contract:
    contract = Contract(
        **payload.model_dump(), status=ContractStatus.PENDING_PAYMENT.value
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract
