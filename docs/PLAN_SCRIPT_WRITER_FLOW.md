# Plan: Tuning Script Writer for Account / Flow-Based Prompts

**Goal:** Support OBD flows that have specific steps (e.g. welcome prompt, product description, subscription prompt, thanks prompt) and either (1) tune the Script Writer per account, or (2) feed a voice flow / flowchart and get prompts per step.

**Constraint for this plan:** Changes only in the **Script Writer** agent—no pipeline or audio changes yet. Downstream impact is noted so we can decide later.

---

## Current state

**Script Writer today:**

- **Input:** `product_brief`, `market_analysis`, `language_override` (and for revision: `feedback`, `previous_scripts`).
- **Output (fixed shape):** For each variant, one object with:
  - `hook` – first 5 seconds, grab attention
  - `body` – 15–18 seconds, product pitch
  - `cta` – 5–7 seconds, DTMF call to action
  - `fallback_1` – if no DTMF, urgency follow-up
  - `fallback_2` – if still no DTMF, persuasion
  - `polite_closure` – graceful exit
  - `full_script` – hook + body + cta concatenated

**Downstream (for context only; no changes in this plan):**

- **Audio Producer** expects exactly these keys: `hook`, `full_script`, `fallback_1`, `fallback_2`, `polite_closure` (and builds `full_script` from hook+body+cta if missing).
- **Pipeline** passes Script Writer output to Eval Panel, then Voice Selector, then Audio Producer.

So today the “flow” is fixed: hook → body → cta (main call), then fallback_1 → fallback_2 → polite_closure.

---

## Your flow vs current structure

Your OBD flow sounds like:

- **Welcome prompt**
- **Product description / subscription prompt** (what to say about the product and how to subscribe)
- **Thanks prompt**
- (possibly more steps)

Rough mapping to current fields:

| Your step              | Current field(s)   | Notes                                      |
|------------------------|--------------------|--------------------------------------------|
| Welcome                | `hook`             | Same idea: open the call, grab attention   |
| Product + subscription | `body` + `cta`     | Body = pitch, CTA = “Press 1 to subscribe” |
| Thanks                 | `polite_closure`   | Same idea: thank and goodbye               |

So **yes, it is possible** to drive the Script Writer from “our flow” (welcome / product-subscription / thanks) and still stay compatible with the rest of the pipeline by mapping your steps to these fields. We can also support **per-account** or **flowchart-driven** definitions of steps and still keep the same output shape if we want zero downstream changes.

---

## Option A: Account-based flow config (tune per account)

**Idea:** Each account (or campaign type) has a **flow definition**: ordered list of steps. The Script Writer is given this flow + product + market and generates one prompt per step.

**Input (new, in addition to product_brief and market_analysis):**

- `flow_config` or `account_flow` – e.g.:

```json
{
  "steps": [
    { "id": "welcome", "purpose": "Greet caller warmly", "max_words": 25 },
    { "id": "product_description", "purpose": "Describe product and benefit", "max_words": 50 },
    { "id": "subscription", "purpose": "DTMF to subscribe (e.g. Press 1)", "max_words": 20 },
    { "id": "thanks", "purpose": "Thank and close", "max_words": 15 }
  ]
}
```

**Script Writer behavior:**

- System prompt is **tuned** to: hu step. Use product and market context. Output JSON with one key per step id.”
- Output can be either:
  - **Flow-shaped:** `{ "welcome": "...", "product_description": "...", "subscription": "...", "thanks": "..." }`  
    Then something (later, or inside Script Writer) maps these to `hook`, `body`, `cta`, `polite_closure`, etc., so audio and pipeline keep working.
  - **Pipeline-shaped:** Script Writer **internally** maps the flow steps to the existing keys (e.g. welcome→hook, product_description→body, subscription→cta, thanks→polite_closure, and optionally “if no DTMF” steps→fallback_1, fallback_2). Then output stays exactly as today and **no other component needs to change**.

**Feasibility:** Yes, with Script Writer only. We only add an optional input (`flow_config`) and tune the system prompt (and optionally the output schema). If we always emit the same keys as today, no pipeline/audio changes.

---

## Option B: Flowchart / flow as input (voice flow or diagram)

**Idea:** User provides a **voice flow** or **flowchart** (structure of the call). The Script Writer produces the actual prompt text for each step.

**Input (new):**

- **Structured flow (JSON)** – same as Option A, e.g. list of steps with id, purpose, max_words.
- **Or flowchart description (text)** – e.g. “Flow: Welcome → Product description → Subscription (Press 1) → Thanks.” We could either:
  - Parse this in a thin layer and turn it into the same structured list of steps, then pass to Script Writer, or
  - Pass the text directly to the Script Writer and say in the system prompt: “Below is a description of the call flow. Generate one prompt per step. Output JSON with keys matching the step names.”

**Script Writer behavior:**

- Receives: flow (structured or text) + product_brief + market_analysis (+ language).
- System prompt: “Given this OBD flow [flow], generate the exact prompt text for each step. Use product and market context. Output JSON: one key per step.”
- Output: either flow-shaped (one key per step) or, again, mapped to the existing hook/body/cta/fallback_1/fallback_2/polite_closure so pipeline and audio stay unchanged.

**Feasibility:** Yes, with Script Writer only. If the flow is given as text, the Script Writer can still output structured JSON (step name → prompt). If we want to avoid any downstream change, we again map step names to the fixed keys inside the Script Writer.

---

## Recommended direction (Script Writer only)

1. **Introduce an optional “flow” input** to the Script Writer:
   - Either **structured** (list of steps with id, purpose, max_words) – from account config or from a future flowchart parser.
   - Or **text** (e.g. “Welcome → Product description → Subscription → Thanks”) that the LLM interprets as steps.

2. **Tune the Script Writer system prompt** so that:
   - When a flow is provided, it generates **one prompt per step** according to that flow.
   - It still uses product_brief and market_analysis for content and tone.
   - It still uses the same emotion tags and language/transliteration rules.

3. **Keep pipeline compatibility:**  
   Script Writer **maps** flow steps to the existing output keys:
   - Step 1 (e.g. welcome) → `hook`
   - Steps 2…N-1 (e.g. product, subscription) → combined or split into `body` and `cta` (e.g. last “action” step → `cta`, rest → `body`)
   - Last step (e.g. thanks) → `polite_closure`
   - Optional: “if no DTMF” steps → `fallback_1`, `fallback_2`  
   So the rest of the pipeline and Audio Producer see the same shape as today.

4. **Account-specific behavior:**  
   “Tuning per account” = passing a different `flow_config` (or flow text) per account/campaign. Same Script Writer code; only the input changes. Optionally we could later store flow configs in DB or config and pass the right one by account_id.

---

## What stays out of scope (for this plan)

- No changes to Market Researcher, Voice Selector, Audio Producer, or orchestrator in this phase.
- No new API or UI; we only define how the Script Writer’s **input** and **prompt** would change. When we implement, we’d add a way to pass flow (e.g. from pipeline payload or from a future “flow editor”).
- No flowchart **visual** parser (e.g. image/diagram → steps); that can be a later phase. For “flowchart input” we limit to text or JSON.

---

## Summary

| Question | Answer |
|----------|--------|
| Can we tune the Script Writer per account? | Yes. Pass a per-account **flow config** (list of steps) and tune the system prompt so it generates prompts per step. |
| Can we feed a voice flow / flowchart and get prompts per step? | Yes. Feed flow as structured JSON or as text; Script Writer generates one prompt per step. |
| Can we do this with **only** the Script Writer changed? | Yes. New optional input (flow), tuned system prompt, and internal mapping from flow steps to existing keys (hook, body, cta, fallback_1, fallback_2, polite_closure) so no other component needs to change. |
| Do we need to change anything else? | No, if we keep the same output shape. If we ever want to expose “flow-shaped” output (e.g. welcome, product_description, thanks) to the rest of the app, then API/UI/audio would need to understand those keys later. |

No code changes in this doc—plan only. When you’re ready to implement, we can start with Option A (structured flow_config) and one mapping strategy (e.g. first step→hook, next-to-last action→cta, last→closure).

---

## Example: Your flow (Welcome → Product description → Thank you)

### 1. How you feed the input

**Option A – Preset in the UI (recommended for v1)**  
- In the app, add a **Call flow** selector (e.g. dropdown or cards) with presets:
  - **Simple 3-step:** Welcome → Product description → Thank you *(your flow)*
  - **Standard OBD:** Welcome → Product description → Subscribe (Press 1) → Thank you
  - **Custom:** (later) paste or type steps, e.g. `welcome, product description, thank you`
- When you choose **Simple 3-step**, the frontend sends the corresponding `flow_config` in the generate request. You don't touch JSON; the app does it.

**Option B – API**  
- The generate API accepts an optional `flow_config` (or `flow`). Example for your flow:

```json
{
  "steps": [
    { "id": "welcome", "purpose": "Greet caller warmly, say who is calling", "max_words": 25 },
    { "id": "product_description", "purpose": "Describe the product and main benefit", "max_words": 60 },
    { "id": "thank_you", "purpose": "Thank the caller and close politely", "max_words": 15 }
  ]
}
```

- If the UI uses presets, it just sends the preset's JSON. Integrations can send their own JSON.

**Option C – Simple text (later)**  
- A single text field: e.g. `Welcome, Product description, Thank you` (comma- or newline-separated). Backend parses this into the same step list and builds `flow_config`. No JSON for the user.

---

### 2. How scripts are generated

1. **Orchestrator** receives product text, country, telco, language, and (when chosen) `flow_config` for "Welcome → Product description → Thank you".
2. **Product Analyzer** and **Market Researcher** run as today → `product_brief`, `market_analysis`.
3. **Script Writer** is called with `product_brief`, `market_analysis`, `language_override`, and **flow_config** = the 3 steps above.
4. **Script Writer** system prompt (when flow is present): *"This call has 3 steps: welcome, product_description, thank_you. Generate the exact prompt text for each step. Use product and market context. Respect max_words. Use emotion tags as before."*
5. **LLM returns** something like:
   - `welcome`: *"Hi, this is [Telco] with a quick message for you…"*
   - `product_description`: *"We're offering EVA — an AI that answers your calls when you're busy…"*
   - `thank_you`: *"Thank you for your time. Have a great day. Goodbye."*
6. **Script Writer maps** these to the **existing** output shape (so pipeline and audio stay unchanged):
   - Step 1 (welcome) → **hook**
   - Step 2 (product_description) → **body** (no separate CTA step, so **cta** = `""`)
   - Step 3 (thank_you) → **polite_closure**
   - No DTMF step → **fallback_1** and **fallback_2** = `""` (or one short "We'll send you more info by SMS" if you want a single follow-up line)
   - **full_script** = hook + body + cta (i.e. welcome + product; cta empty)
7. **Eval Panel** and **Voice Selector** see the same script structure as today; no changes needed.

---

### 3. How audio is generated

- **Audio Producer** already expects: `hook`, `full_script`, `fallback_1`, `fallback_2`, `polite_closure`.
- For your 3-step flow:
  - **Hook previews** use `hook` = welcome text.
  - **Main message** = `full_script` = welcome + product description (one continuous segment).
  - **Fallbacks**: if `fallback_1` / `fallback_2` are empty, the producer **skips** them (existing logic: `if not text.strip(): continue`). So no "Press 1" or extra segments.
  - **Closure** = `polite_closure` = thank you.
- Result: one linear playback — **welcome → product description → thank you** — with no DTMF branching. No changes required in the Audio Producer.

---

### 4. End-to-end summary (your flow)

| Step | What happens |
|------|-----------------------------|
| **You** | Select "Simple 3-step" (or send flow_config with welcome, product_description, thank_you). |
| **Pipeline** | Product + market as today; Script Writer gets flow_config and generates 3 prompts, then maps to hook / body / polite_closure (cta and fallbacks empty). |
| **Scripts** | Same shape as today: hook, body, cta, full_script, fallback_1, fallback_2, polite_closure. |
| **Audio** | Main = welcome + product; closure = thank you; fallbacks skipped. |

So: **you only feed the flow (preset or JSON); scripts and audio are generated to match that flow, and the rest of the system stays unchanged.**

---

## Best approach (implementation order)

1. **Start with Option A (structured flow_config)**  
   - Add an optional `flow_config` to the Script Writer: list of steps with `id`, `purpose`, `max_words`.  
   - When **absent**: keep current behavior (single hook/body/cta/fallbacks/closure). No breaking changes.  
   - When **present**: system prompt says "generate one prompt per step"; then map steps → existing keys.

2. **Use a single, explicit mapping** (inside Script Writer only):
   - Step 1 → `hook`
   - Middle steps (product, subscription, etc.) → concatenate into `body`; last "action" step (e.g. "Press 1") → `cta`
   - Last step (e.g. thanks) → `polite_closure`
   - Optionally reserve step ids like `fallback_if_no_dtmf` → `fallback_1`, `fallback_2`, or keep fallbacks as today (LLM-generated based on CTA).

3. **Add flow text later (Option B)**  
   - Once structured flow works, allow a **text** flow (e.g. "Welcome → Product → Subscribe → Thanks"). Either:  
     - Parse in a thin layer into the same step list and pass as `flow_config`, or  
     - Pass text to the LLM and ask for JSON with one key per step, then map that JSON to the same keys.  
   - No need for flowchart/image parsing in v1.

4. **Per-account tuning**  
   - "Per account" = different `flow_config` per request (from API payload or, later, from DB/config keyed by account_id). Same code path; only the input changes.

**Summary:** Implement **Option A first** (optional structured `flow_config` + mapping to current keys). Add **Option B** (flow as text) when needed. No pipeline or audio changes; Script Writer remains the only modified component.
