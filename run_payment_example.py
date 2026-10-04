"""Send one high-risk payment through both AI capabilities and print its cost ledger."""

from fintech_cost_service.infrai_ai import InfraiAI
from fintech_cost_service.payment_workflow import PaymentEvent, process_payment


def main() -> None:
    event = PaymentEvent(
        event_id="pay_demo_1042",
        amount_usd="12500.00",
        merchant="Northwind Securities",
        customer_country="US",
        attempts_10m=2,
    )
    ai = InfraiAI()
    outcome = process_payment(
        event,
        generate_notification=ai.generate_notification,
        generate_embedding=ai.generate_embedding,
    )
    print(outcome.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
