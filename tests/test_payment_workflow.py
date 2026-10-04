from decimal import Decimal

from fintech_cost_service.payment_workflow import (
    EmbeddingCall,
    PaymentEvent,
    RiskAction,
    TextCall,
    process_payment,
)


def test_high_value_payment_is_held_and_both_call_costs_are_recorded() -> None:
    prompts: list[str] = []
    audit_records: list[str] = []

    def notification(prompt: str) -> TextCall:
        prompts.append(prompt)
        return TextCall(
            content="Hold pay_900 for review: high amount or repeated attempts.",
            cost_usd=Decimal("0.0041"),
            vendor="notification-vendor",
        )

    def embedding(record: str) -> EmbeddingCall:
        audit_records.append(record)
        return EmbeddingCall(
            embedding=[0.25, -0.5, 0.75],
            cost_usd=Decimal("0.0003"),
            vendor="embedding-vendor",
        )

    outcome = process_payment(
        PaymentEvent(
            event_id="pay_900",
            amount_usd="12000.00",
            merchant="Example Brokerage",
            customer_country="GB",
            attempts_10m=1,
        ),
        generate_notification=notification,
        generate_embedding=embedding,
    )

    assert outcome.action is RiskAction.HOLD
    assert outcome.total_model_cost_usd == Decimal("0.0044")
    assert outcome.serving_vendors == ["notification-vendor", "embedding-vendor"]
    assert "action=hold" in prompts[0]
    assert "notification=Hold pay_900" in audit_records[0]
