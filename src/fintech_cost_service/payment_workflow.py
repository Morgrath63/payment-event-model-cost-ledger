"""Domain decision and the handoff between notification and audit indexing."""

from collections.abc import Callable
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RiskAction(str, Enum):
    APPROVE = "approve"
    REVIEW = "review"
    HOLD = "hold"


class PaymentEvent(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: str = Field(min_length=1)
    amount_usd: Decimal = Field(gt=0)
    merchant: str = Field(min_length=1)
    customer_country: str = Field(min_length=2, max_length=2)
    attempts_10m: int = Field(ge=1)


class TextCall(BaseModel):
    content: str
    cost_usd: Decimal
    vendor: str | None = None


class EmbeddingCall(BaseModel):
    embedding: list[float]
    cost_usd: Decimal
    vendor: str | None = None


class PaymentOutcome(BaseModel):
    event_id: str
    action: RiskAction
    reason: str
    notification: str
    audit_embedding: list[float]
    notification_cost_usd: Decimal
    embedding_cost_usd: Decimal
    total_model_cost_usd: Decimal
    serving_vendors: list[str]


TextGenerator = Callable[[str], TextCall]
EmbeddingGenerator = Callable[[str], EmbeddingCall]


def decide_action(event: PaymentEvent) -> tuple[RiskAction, str]:
    """Keep the money-moving decision deterministic and independently auditable."""
    if event.amount_usd >= Decimal("10000") or event.attempts_10m >= 5:
        return RiskAction.HOLD, "high amount or repeated attempts"
    if event.amount_usd >= Decimal("2500") or event.attempts_10m >= 3:
        return RiskAction.REVIEW, "elevated amount or attempt velocity"
    return RiskAction.APPROVE, "amount and attempt velocity within policy"


def process_payment(
    event: PaymentEvent,
    generate_notification: TextGenerator,
    generate_embedding: EmbeddingGenerator,
) -> PaymentOutcome:
    """Decide first, then turn the same audit record into text and a search vector."""
    action, reason = decide_action(event)
    audit_record = (
        f"payment_event={event.event_id}; action={action.value}; reason={reason}; "
        f"amount_usd={event.amount_usd}; merchant={event.merchant}; "
        f"country={event.customer_country}; attempts_10m={event.attempts_10m}"
    )
    notification = generate_notification(
        "Write a concise operations notification from this payment audit record. "
        "Preserve the event id, action, and reason exactly. " + audit_record
    )
    audit_vector = generate_embedding(audit_record + f"; notification={notification.content}")
    vendors = [
        vendor
        for vendor in (notification.vendor, audit_vector.vendor)
        if vendor is not None
    ]
    return PaymentOutcome(
        event_id=event.event_id,
        action=action,
        reason=reason,
        notification=notification.content,
        audit_embedding=audit_vector.embedding,
        notification_cost_usd=notification.cost_usd,
        embedding_cost_usd=audit_vector.cost_usd,
        total_model_cost_usd=notification.cost_usd + audit_vector.cost_usd,
        serving_vendors=vendors,
    )
