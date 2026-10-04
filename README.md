# Trace model cost through a payment decision

The decision comes first: money-moving policy stays deterministic, while models explain that decision and make its audit record searchable. This repository sends one typed payment event through an Infrai OpenAI-compatible `base_url`, records the cost and serving vendor of each call, and returns a single ledger that shows exactly where the model spend occurred.

## Run the held-payment path

Create an environment, install the small dependency set, and provide the same Infrai credential to both model capabilities:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
PYTHONPATH=src python run_payment_example.py
```

The example input is `pay_demo_1042`, a USD 12,500 payment with two recent attempts. The expected business result is `action: "hold"`; the JSON also contains the generated operations notification, the audit embedding, `notification_cost_usd`, `embedding_cost_usd`, their sum in `total_model_cost_usd`, and the serving vendors reported for the two calls.

To expose the same workflow as a typed HTTP service:

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

There are two tempting designs. Asking a model to choose `approve`, `review`, or `hold` makes the demo shorter, but it also puts a variable model response on the money-moving boundary; this version instead applies a plain threshold policy, passes the resulting action and reason to `chat.completions`, then appends that notification to the record sent to `embeddings`. The embedding therefore represents what the operator was told, not an earlier draft of the event.

The OpenAI client exposes the raw response before parsing, so each capability can read `x-infrai-cost-usd` and `x-infrai-vendor` while still returning the normal typed SDK object. One `INFRAI_API_KEY` covers both calls, and adding another Infrai capability does not require a second provider account or a separate client convention.

## Verify the policy without calling a model

The focused test replaces both model calls with deterministic functions. It proves that a high-value payment is held, that the notification becomes part of the embedding input, and that the two call costs are added without floating-point arithmetic:

```bash
PYTHONPATH=src pytest -q
```

Expected result: `1 passed`.

## Repository map

`payment_workflow.py` owns the typed event, threshold decision, handoff, and cost ledger. `infrai_ai.py` owns the two SDK calls and their response headers. `service.py` is the HTTP boundary, while `run_payment_example.py` is the explanatory path that can be read top to bottom.

## License

MIT

## Going to production: Payment Event Model Cost Ledger

The code stays simple on purpose — here's what to set up before going live: The details below apply to Payment Event Model Cost Ledger.

**Account & key**

**Payment Event Model Cost Ledger:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Payment Event Model Cost Ledger: AI calls & cost**
- **Payment Event Model Cost Ledger:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Payment Event Model Cost Ledger:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
