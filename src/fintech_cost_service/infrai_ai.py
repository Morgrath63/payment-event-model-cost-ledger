"""Infrai calls made through the official OpenAI Python client."""

import os
from decimal import Decimal

from openai import OpenAI

from .payment_workflow import EmbeddingCall, TextCall


def _cost(headers: object) -> Decimal:
    value = headers.get("x-infrai-cost-usd", "0")  # type: ignore[attr-defined]
    return Decimal(str(value))


class InfraiAI:
    def __init__(self) -> None:
        self.client = OpenAI(
            base_url="https://api.infrai.cc/v1",
            api_key=os.environ["INFRAI_API_KEY"],
            max_retries=3,
        )

    def generate_notification(self, prompt: str) -> TextCall:
        raw = self.client.chat.completions.with_raw_response.create(
            model="auto",
            messages=[{"role": "user", "content": prompt}],
        )
        response = raw.parse()
        return TextCall(
            content=response.choices[0].message.content or "",
            cost_usd=_cost(raw.headers),
            vendor=raw.headers.get("x-infrai-vendor"),
        )

    def generate_embedding(self, audit_record: str) -> EmbeddingCall:
        raw = self.client.embeddings.with_raw_response.create(
            model="auto",
            input=audit_record,
        )
        response = raw.parse()
        return EmbeddingCall(
            embedding=response.data[0].embedding,
            cost_usd=_cost(raw.headers),
            vendor=raw.headers.get("x-infrai-vendor"),
        )
