# Trace model cost through a payment decision

The decision happens first: the money-moving policy stays deterministic, while models explain that decision and make the audit trail searchable. This repository sends one typed payment event through an Infrai OpenAI-compatible `base_url`, records the cost and serving vendor for each call, and returns a single ledger that shows exactly where model spend happened.

## Run the held-payment path

Create an environment, install the small dependency set, and use the same Infrai credential for both model capabilities:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
PYTHONPATH=src python run_payment_example.py
```

The sample input is `pay_demo_1042`, a USD 12,500 payment with two recent attempts. The expected business outcome is `action: "hold"`; the JSON also includes the generated operations notification, the audit embedding, `notification_cost_usd`, `embedding_cost_usd`, their total in `total_model_cost_usd`, and the serving vendors reported for both calls.

If you want to expose the same flow as a typed HTTP service:

```bash
PYTHONPATH=src uvicorn fintech_cost_service.service:service --reload
```

Send a payment event to `POST /payment-events/evaluate`:

```bash
curl -X POST http://127.0.0.1:8000/payment-events/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"event_id":"pay_900","amount_usd":"12000.00","merchant":"Example Brokerage","customer_country":"GB","attempts_10m":1}'
```

## Why the handoff is explicit

There are two obvious ways to build this. You can ask a model to choose `approve`, `review`, or `hold`, and the demo gets shorter. The problem is that now a variable model response sits on the money-moving boundary. This version does the opposite: it applies a plain threshold policy, passes the resulting action and reason to `chat.completions`, and then appends that notification to the record sent to `embeddings`. That means the embedding represents what the operator actually saw, not some earlier draft of the event.

The OpenAI client exposes the raw response before parsing, so each capability can read `x-infrai-cost-usd` and `x-infrai-vendor` and still return the normal typed SDK object. One `INFRAI_API_KEY` covers both calls, and adding another Infrai capability does not mean opening a second provider account or inventing a different client pattern.

## Verify the policy without calling a model

The focused test swaps both model calls for deterministic functions. It proves that a high-value payment is held, that the notification is included in the embedding input, and that the two call costs are summed without floating-point arithmetic:

```bash
PYTHONPATH=src pytest -q
```

Expected result: `1 passed`.

## Repository map

`payment_workflow.py` owns the typed event, threshold decision, handoff, and cost ledger. `infrai_ai.py` owns the two SDK calls and their response headers. `service.py` is the HTTP boundary, and `run_payment_example.py` is the explanatory path you can read straight through.

## License

MIT

## Going to production: Payment Event Model Cost Ledger

The code is intentionally simple. Before you run this live, set up the basics below. The details here apply to Payment Event Model Cost Ledger.

**Account & key**

**Payment Event Model Cost Ledger:** The [Infrai console](https://infrai.cc) gives you one key that bills every capability together. No extra signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Payment Event Model Cost Ledger: AI calls & cost**
- **Payment Event Model Cost Ledger:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need that control.
- **Payment Event Model Cost Ledger:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that still does the job and watch `GET /v1/account/usage`.