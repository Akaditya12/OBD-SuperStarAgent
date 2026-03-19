# How the Market Researcher works (manual flow)

The **Market Researcher** is Agent 2. It takes **country**, **telco**, and a **product brief**, sends one request to **Azure OpenAI**, and returns a structured **market analysis** (JSON) that the Script Writer and other agents use.

---

## 1. What it does in code

1. **Inputs** (from the pipeline or from your debug call):
   - `country` – e.g. `"Nigeria"`, `"Ethiopia"`
   - `telco` – e.g. `"MTN"`, `"Airtel"`
   - `product_brief` – dict with at least `product_name` and `description` (and any other keys from the Product Analyzer)

2. **Builds the user prompt** (see `market_researcher.py`):
   - Literal text: `COUNTRY: {country}`, `TELCO OPERATOR: {telco}`, then `PRODUCT BEING PROMOTED:` plus `json.dumps(product_brief, indent=2)`.
   - Asks for a comprehensive market analysis and “Output only valid JSON.”

3. **Calls the LLM** via `BaseAgent.call_llm()`:
   - **System prompt**: the long `SYSTEM_PROMPT` in `market_researcher.py` (expert market analyst, African/emerging telecoms, required JSON structure).
   - **User prompt**: the string above.
   - **API**: Azure OpenAI (`AsyncAzureOpenAI`) using `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` from config (`.env`).

4. **Parses and returns**:
   - Reads the model reply, strips markdown/code fences if present, `json.loads(...)` into a dict.
   - That dict is the **market_analysis** (market_overview, cultural_insights, target_audience_psyche, promotion_recommendations, etc.).

So at code level: **Market Researcher = one Azure OpenAI chat call with a fixed system prompt and a user message built from country, telco, and product_brief.**

---

## 2. Call it manually with curl (debug endpoint)

Backend must be running on `http://localhost:8000`. If auth is enabled, add `-b cookies.txt` after logging in.

**Minimal (country + telco only; product_brief is filled with a default):**

```bash
curl -s -X POST http://localhost:8000/api/debug/market-research \
  -H "Content-Type: application/json" \
  -d '{"country": "Nigeria", "telco": "MTN"}'
```

**With your own product brief (same shape the pipeline uses):**

```bash
curl -s -X POST http://localhost:8000/api/debug/market-research \
  -H "Content-Type: application/json" \
  -d '{
    "country": "Nigeria",
    "telco": "MTN",
    "product_brief": {
      "product_name": "Weekend Data Bundle",
      "description": "5GB for 48 hours. Unlimited social media. Dial *123# to activate.",
      "key_features": ["5GB data", "48 hours", "Unlimited WhatsApp"]
    }
  }'
```

**Pretty-print the JSON response:**

```bash
curl -s -X POST http://localhost:8000/api/debug/market-research \
  -H "Content-Type: application/json" \
  -d '{"country": "Nigeria", "telco": "MTN"}' | python3 -m json.tool
```

---

## 3. What the response contains

The endpoint returns:

- **`market_analysis`** – The same structure the pipeline uses: `country`, `telco`, `market_overview`, `cultural_insights`, `current_affairs`, `target_audience_psyche`, `competitive_landscape`, `promotion_recommendations`, etc.
- **`system_prompt`** – Exact system prompt sent to the LLM (so you can see the instructions and JSON schema).
- **`user_prompt`** – Exact user message (country, telco, product_brief text).

So you can see **exactly** what the Market Researcher sends to the OpenAI API and what it gets back.

---

## 4. How the pipeline uses it

In the normal flow (`/api/generate/start`):

1. Orchestrator runs **Product Analyzer** and **Market Researcher** in parallel (when there’s no cache).
2. For Market Researcher it passes:
   - `country`, `telco` from the request,
   - `product_brief = {"product_name": "pending", "description": product_text[:500]}` (so it doesn’t wait for the full product brief).
3. The returned **market_analysis** is stored in the pipeline result and passed to the **Script Writer** (and used for voice/context later).

The debug endpoint runs **only** the Market Researcher with the body you send; no Product Analyzer, no cache, no Script Writer.

---

## 5. Files to read

| File | What to look at |
|------|------------------|
| `backend/agents/market_researcher.py` | `SYSTEM_PROMPT`, `run()`, how `user_prompt` is built and `call_llm` / `parse_json` are used. |
| `backend/agents/base.py` | `call_llm()` (builds Azure client, sends messages, returns text) and `parse_json()`. |
| `backend/config.py` | `AZURE_OPENAI_*` – where the API key and deployment come from. |

Using the curl above and these files, you can trace the full path from your JSON body → user prompt → Azure OpenAI → market_analysis.
