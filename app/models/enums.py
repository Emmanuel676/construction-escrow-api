from enum import Enum


class ContractStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    ESCROW_LOCKED = "ESCROW_LOCKED"


class OrderStatus(str, Enum):
    AWAITING_FULFILLMENT = "AWAITING_FULFILLMENT"
    PAID_PROCESSING = "PAID_PROCESSING"


class PaymentType(str, Enum):
    ESCROW_LOCK = "ESCROW_LOCK"
    STORE_PURCHASE = "STORE_PURCHASE"


class TransactionStatus(str, Enum):
    SUCCESS = "SUCCESS"
