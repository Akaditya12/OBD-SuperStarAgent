# Plan: Account Flows (e.g. BTC Christianity) + Regenerate Script / Keep Voice

**Goals:**
1. Support **account-specific OBD flows** with multiple prompts and multiple DTMF options (e.g. BTC Botswana Christianity: welcome → pack details (Press 1/2/3) → thanks).
2. Let the user get the **desired flow every time** by feeding the right data and/or flow config.
3. Add **“Regenerate script only, keep voice”** so the user can re-run script generation while keeping the same ElevenLabs (or other) voice choice.

---

## 1. Your example: BTC Botswana Christianity

**Flow (3 prompts):**

| # | Timing   | Content |
|---|----------|--------|
| 1 | 0:00–0:16 | Welcome verse + product pitch + “Press 1 to activate now.” |
| 2 | 0:00–0:07 | Pack details: Press 1 = 2 pula daily, Press 2 = 5 pula weekly, Press 3 = 10 pula monthly. |
| 3 | 0:00–0:09 | Thanks + “You have activated BTC Christianity Portal” + “Dial 1195 anytime” + “Remember 1195.” |

**Fixed data:**
- **Shortcode / CTA:** `Press 1 to activate now` (prompt 1); `Press 1 / 2 / 3` for packs (prompt 2); `Dial 1195`, `Remember 1195` (prompt 3).
- **Pricing:** 2 pula daily, 5 pula weekly, 10 pula monthly.
- **Service:** BTC Christianity Portal, Bible narrations, shortcode 1195.
- **Language:** English.

Today the pipeline produces **one** linear script (hook + body + cta + fallbacks + closure). It does **not** produce three separate prompts or multiple DTMF options in one step. So we need both “what to do with the current UI” and “how to support this flow properly later.”

---

## 2. Best approach (phased)

### Phase 1: Use the current interface to get “good enough” for BTC

**What to feed in the UI (today):**

- **Product preset:** Christianity Portal (or Custom).
- **Product Documentation** – put everything the script must mention in one place, with clear sections so the Product Analyzer and Script Writer can use it:
  - **Product name:** BTC Christianity Portal.
  - **Overview:** e.g. “Complete narrations of the Holy Bible anytime, anywhere. Exclusive on BTC.”
  - **Key features:** Bible narrations, daily/weekly/monthly packs, shortcode 1195.
  - **Shortcode / CTA:**  
    `Press 1 to activate. Press 1 for daily pack (2 pula), Press 2 for weekly (5 pula), Press 3 for monthly (10 pula). Dial 1195 to access; remember 1195.`
  - **Pricing:**  
    `Daily 2 BWP, Weekly 5 BWP, Monthly 10 BWP.`

- **Target Country:** Botswana  
- **Telco:** BTC  
- **Language Override:** English  

**What you get today:**  
One script (hook + body + cta + fallbacks + closure) that should mention activation, pack options (1/2/3), prices (2/5/10 pula), and 1195. It will **not** be split into three separate prompts; that requires Phase 2.

**Limitation:**  
The pipeline outputs a **single** `full_script` (and hook/body/cta). To have three **separate** audio files (welcome, pack menu, thanks), we need either:
- flow_config with **multiple steps** and the audio pipeline to render **one segment per step**, or  
- you manually split the generated script into three parts and use Script-to-Voice (or similar) for each.

---

### Phase 2: Flow-aware scripts and multi-step audio (per account)

This is the “perfect way” so **each account gets its desired flow every time**.

**2a. Extend flow_config (see also `PLAN_SCRIPT_WRITER_FLOW.md`)**

- Support **multiple steps** and **multiple DTMF options** in one step.
- Example for BTC Christianity:

```json
{
  "steps": [
    { "id": "welcome", "purpose": "Welcome with verse; pitch Bible portal; Press 1 to activate", "max_words": 40 },
    { "id": "pack_details", "purpose": "Press 1 = daily 2 pula, Press 2 = weekly 5 pula, Press 3 = monthly 10 pula", "max_words": 35 },
    { "id": "thanks", "purpose": "Thank; confirm activation; dial 1195 anytime; remember 1195", "max_words": 25 }
  ]
}
```

- Script Writer generates **one prompt per step** (using product + market + pricing/shortcode from the brief).
- Either:
  - **Option A:** Script Writer still outputs the **current shape** (hook, body, cta, polite_closure, …) by **mapping** steps into those fields (e.g. step1→hook, step2→body, step3→polite_closure), and we **concatenate** for one `full_script` so audio stays one block; or  
  - **Option B:** Script Writer outputs **one blob per step** and the **Audio Producer** (and API) support **multiple segments** (e.g. `prompt_1`, `prompt_2`, `prompt_3`) so you get three separate audio files and the IVR can play them in sequence.

**2b. Where flow_config comes from**

- **Per account/campaign:** Either in the **generate request** (e.g. `flow_config` in the body when starting the pipeline) or from **DB** (e.g. `account_flows` or `campaign_flows` keyed by account_id or campaign_type).
- **UI:** A “Flow” selector (e.g. “BTC Christianity 3-step”) that sends the right `flow_config`, or a small “Flow” editor (steps + purposes) that builds the JSON. No change to the rest of the form.

**2c. Data you feed**

- Same as today: **Product Documentation** (overview, features, **Shortcode/CTA**, **Pricing**).
- Plus either:
  - **Preset flow** (e.g. “BTC Christianity”) that the UI/API maps to the JSON above, or  
  - **Explicit flow_config** (steps + purposes) in the request or from DB.

So: **product text + flow_config (per account)** = desired flow every time.

---

### Phase 3: Regenerate script only (keep voice)

**Current behaviour:**

- **Regenerate audio:** You can regenerate **audio** for a variant (same script, same or default voice/engine). So: “same script, new audio” is supported.
- **Regenerate script:** If you run the **full pipeline again**, you get **new scripts and new voice selection**; you cannot “regenerate script only and keep my chosen voice.”

**Gap:**  
“I like the ElevenLabs voice but not the script” → today you must either re-run the whole pipeline (and lose the locked voice) or edit the script by hand and then regenerate audio. So **“regenerate script only, keep voice”** is not possible in the current setup.

**Proposed behaviour:**

- **“Regenerate script”** (e.g. a button on the results step):  
  - Re-run **only** Script Writer (and optionally Eval + Revision) using the **same** product_brief, market_analysis, language, and (when we have it) flow_config.  
  - **Keep** the current **voice selection** (and hook previews / engine) so that when the user then generates (or regenerates) audio, we use the **same** voice with the **new** script.

**Implementation outline:**

- **Backend:** New endpoint or mode, e.g. `POST /api/sessions/{session_id}/regenerate-scripts` that:
  - Accepts optional overrides (e.g. tweaked product text or flow_config).
  - Re-runs Product Analyzer (if input changed) or reuses cached product_brief; re-runs Market Researcher or reuses cached market_analysis.
  - Re-runs Script Writer (and optionally Eval + Revision).
  - **Does not** re-run Voice Selector: keep existing `voice_selection` (and hook_previews) in the session.
  - Returns updated `initial_scripts` / `final_scripts`; session still has same `voice_selection` and hook_previews.
- **Frontend:** On the results step, add a **“Regenerate script only”** (or “New script, same voice”) button that calls this endpoint, then refreshes the script UI and keeps the current voice/previews. Optionally: “Regenerate script” could open a small modal to tweak product text or flow before re-running.

**Optional (later):**  
- “Regenerate audio only” (same script, different voice) = change voice selection then call existing regenerate-audio.  
- “Change voice only” (same script, new voice) = same as above if we persist “selected voice” and allow changing it without re-running the full pipeline.

---

## 3. Summary table

| Need | Today | After Phase 2 | After Phase 3 |
|------|--------|----------------|----------------|
| BTC 3-prompt flow (welcome, packs, thanks) | One combined script; you can put all text in product doc and get one script that mentions 1/2/3 and 1195 | flow_config with 3 steps → either one script built from 3 parts or 3 segments for audio | Same + regenerate script only |
| Different flows per account | Same pipeline for all; you change product text / shortcode manually | flow_config per account/campaign (from request or DB) | Same |
| “I like the voice, not the script” | Re-run full pipeline (lose voice) or edit script + regenerate audio | Same | **Regenerate script only** keeps voice; then generate/regenerate audio with new script + same voice |
| “I like the script, want different voice” | Change voice and use “Regenerate audio” (if we persist selection) or re-run | Same | Same; can add explicit “Regenerate audio (same script)” with new voice |

---

## 4. Recommended order

1. **Short term (current UI):**  
   Use Phase 1: feed BTC Christianity in Product Documentation (overview, features, Shortcode/CTA with 1/2/3 and 1195, Pricing 2/5/10 BWP), Botswana, BTC, English. You get one script that can mention all of it; split into three prompts manually for IVR if needed.

2. **Next (flows):**  
   Implement **flow_config** in Script Writer (see `PLAN_SCRIPT_WRITER_FLOW.md`): optional list of steps, generate one prompt per step, map to current hook/body/cta/closure (or extend to multi-segment later). Add flow_config to the generate request (and optionally DB) and a flow selector or editor in the UI.

3. **Then (regenerate script):**  
   Add **“Regenerate script only (keep voice)”**: backend endpoint that re-runs script generation only and keeps `voice_selection` and hook_previews; frontend button on results step.

4. **Later (multi-segment audio):**  
   If you need **three separate audio files** for welcome / pack menu / thanks, extend the Audio Producer (and session shape) to support multiple segments per variant (e.g. `prompt_1`, `prompt_2`, `prompt_3`) driven by flow_config.

This keeps the interface tuned and efficient while moving toward per-account flows and the regenerate-script-keep-voice behaviour you want.

---

## 5. Adding new flow configs

**Flow config** = **structure only** (which steps, in what order, and the purpose of each).  
**Product description** = **variable content** (prices, shortcode, CTA, service name). So the same flow can be reused with different product docs (e.g. same 3-step flow, different price points and shortcode).

### How to add a new flow

1. **Admin API (recommended)**  
   As an admin user:
   - **Create:** `POST /api/admin/flow-configs`  
     Body: `{ "account_key": "BTC", "service_key": "Sports", "display_name": "BTC Sports 3-step", "steps": [ { "id": "welcome", "purpose": "...", "max_words": 40 }, ... ], "is_default": false }`
   - **Update:** `PUT /api/admin/flow-configs/{id}`  
     Body: `{ "display_name": "...", "steps": [...], "is_default": true }`

2. **Supabase**  
   - Table Editor: open `flow_configs` → Insert row (account_key, service_key, display_name, steps as JSONB).  
   - Or SQL: `INSERT INTO flow_configs (account_key, service_key, display_name, steps, is_default) VALUES (...);`

3. **Seed script**  
   Edit `scripts/seed_flow_configs.py` to append another flow dict, then run `python3 scripts/seed_flow_configs.py` (uses upsert so existing rows are updated).

After adding, the new flow appears in the **Account flow (optional)** dropdown on the home page. The user still enters **product description** (including Shortcode/CTA and Pricing); the pipeline uses that for the actual numbers and CTAs, and the flow config only for the step structure.
