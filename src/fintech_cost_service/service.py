"""HTTP boundary for payment event evaluation."""

from fastapi import FastAPI

from .infrai_ai import InfraiAI
from .payment_workflow import PaymentEvent, PaymentOutcome, process_payment

service = FastAPI(title="Payment model cost ledger")


@service.post("/payment-events/evaluate", response_model=PaymentOutcome)
def evaluate_payment(event: PaymentEvent) -> PaymentOutcome:
    ai = InfraiAI()
    return process_payment(
        event,
        generate_notification=ai.generate_notification,
        generate_embedding=ai.generate_embedding,
    )
