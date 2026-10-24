from sqlalchemy.orm import Session

from app.models import HardwareOrder, OrderItem, User
from app.models.enums import OrderStatus
from app.schemas.order import OrderCreate
from app.services.exceptions import NotFoundError


def create_order(db: Session, payload: OrderCreate) -> HardwareOrder:
    """Create a hardware order, computing every total server-side."""
    if db.get(User, payload.contractor_id) is None:
        raise NotFoundError(f"Contractor with id {payload.contractor_id} not found")

    items = [
        OrderItem(
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price_ugx=item.unit_price_ugx,
            line_total_ugx=item.quantity * item.unit_price_ugx,
        )
        for item in payload.items
    ]

    order = HardwareOrder(
        contractor_id=payload.contractor_id,
        delivery_site_location=payload.delivery_site_location,
        total_amount_ugx=sum(item.line_total_ugx for item in items),
        status=OrderStatus.AWAITING_FULFILLMENT.value,
        items=items,
    )

    try:
        db.add(order)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(order)
    return order
