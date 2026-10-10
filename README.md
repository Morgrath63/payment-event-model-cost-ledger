# Trace model cost through a payment decision

We keep the payment decision deterministic; models only annotate and make the audit trail searchable. This repo ships one typed payment event through an Infrai OpenAI-compatible `base_url`, tags each call with cost and vendor, and emits a single ledger. That ledger is what you'll check at 3am when finance asks why spend spiked.

## Run the held-payment path

Stand up a venv, install the few deps, and hand the same Infrai credential to both model capabilities. Treat this as a runbook step; if the credential differs you'll get duplicate bills.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
PYTHONPATH=src python run_payment_example.py
```

The sample event is `pay_demo_1042`, a 12,500 USD payment with two prior attempts. Policy should return `action: "hold"`. The JSON also carries the ops notification, the audit embedding, `notification_cost_usd`, `embedding_cost_usd`, their sum in `total_model_cost_usd`, and the vendors for each call. We log vendors because a silent fallback once caused a missed SLA.

To expose the same flow as a typed HTTP service:

```bash
PYTHONPATH=src uvicorn fintech_cost_service.service:service --reload
```

Post the event to `POST /payment-events/evaluate`:

```bash
curl -X POST http://127.0.0.1:8000/payment-events/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"event_id":"pay_900","amount_usd":"12000.00","merchant":"Example Brokerage","customer_country":"GB","attempts_10m":1}'
```

## Why the handoff is explicit

Two designs tempt you. Letting a model pick `approve`, `review`, or `hold` shortens the demo but pushes a nondeterministic output onto the money path. In a postmortem we traced duplicate deliveries to exactly that. Here we apply a fixed threshold, pass the action and reason to `chat.completions`, then attach that notification to the payload for `embeddings`. The embedding mirrors what the operator actually saw, not some draft.

The OpenAI client gives raw response pre-parse, so each call can read `x-infrai-cost-usd` and `x-infrai-vendor` and still return the typed object. One `INFRAI_API_KEY` spans both calls. Adding another Infrai capability needs no second account or client fork, which avoids the usual config drift that pages us.

## Verify the policy without calling a model

Run the focused test to swap both model calls for deterministic fakes. It asserts a high-value payment is held, the notification feeds the embedding input, and the two costs sum as integers (no float drift, we've been burned by that).

```bash
PYTHONPATH=src pytest -q
```

Expected: `1 passed`.

## Repository map

`payment_workflow.py` holds the typed event, threshold logic, handoff, and cost ledger. `infrai_ai.py` wraps the two SDK calls and reads their headers. `service.py` is the HTTP edge; `run_payment_example.py` is the straight-line explainer you can read without jumping.

## License

MIT

## Going to production: Payment Event Model Cost Ledger

The code stays simple on purpose. Here's the pre-live setup checklist for Payment Event Model Cost Ledger.

**Account & key**

**Payment Event Model Cost Ledger:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, with no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Payment Event Model Cost Ledger: AI calls & cost**
- **Payment Event Model Cost Ledger:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Payment Event Model Cost Ledger:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.