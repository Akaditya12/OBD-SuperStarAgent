# OBD SuperStar Agent — Improvements backlog

Prioritized from **quick wins** (done or easy) to **larger initiatives** (team already working or needs design).

---

## Done / quick wins (this sprint)

| Item | Status | Notes |
|------|--------|--------|
| **Expand product description** | Done | Full-screen/large editor so price, short code, tables aren’t missed |
| **ElevenLabs `apply_text_normalization`** | Done | API body `apply_text_normalization: "on"` for consistent number/date handling |
| **Currency hint on country** | Done | Read-only hint (e.g. Zambia → ZMW) to nudge opco-specific pricing later |

---

## Next (medium effort)

| Item | Owner / dependency | Notes |
|------|--------------------|--------|
| **Product as Markdown + tabular** | Ankit suggestion | Prefer tables/bullets over long paragraphs for Product Analyzer prompts; accept `.md` upload; optional “paste as markdown” template |
| **Multi-opco price points** | Product | Separate fields: currency + daily/weekly/monthly packs per country; can extend after currency hint |
| **Dialect correction storage** | Localization | DB table: `original_word`, `correct_word`, `type` (`spelling` \| `phonetic`); API to add/list; later wire into TTS preprocessing |
| **Pronunciation dictionary** | ElevenLabs | Use `pronunciation_dictionary_locators` in TTS payload once dictionary IDs exist |

---

## In progress elsewhere (don’t duplicate)

| Item | Notes |
|------|--------|
| **Full IVR flow as input** | Team building flowchart → prompt from XML/Visio; not only service description |
| **ACP XML → Mermaid flowchart** | Currently basic; keep improving separately |

---

## Later (larger scope)

| Item | Notes |
|------|--------|
| **Localization DB** | Grow dialect corrections over time (like Eva Arabic/Dari/Pashto DB) |
| **AI dialect verification** | STT agent to compare TTS output vs expected local pronunciation |
| **OBD flow simulator** | Web flowchart player with DTMF simulation for account managers pre-deploy |
| **Local resource feedback loop** | Share prompts/audio with Cameroon/Ghana/Tanzania contacts; feed corrections into DB |

---

## Roadmap — Next phase (captured 2026-05-13)

Three connected initiatives discussed with user. Implementation order TBD; sequence below reflects suggested order.

### 1. Flow Config UX — efficiency pass
The current pipeline screen only lets users *pick* an existing flow; creating new flows still needs admin-SQL or the admin panel. Goal: make creating/adjusting flows a first-class action right on the campaign-start screen.
- Inline "Create new flow" with a visual step builder (drag/reorder, set `purpose` + `max_words` per step)
- Show example flows from similar accounts (same country/telco) as starting templates
- Allow cloning an existing flow with one click and editing
- Persists to `flow_configs` via the existing `POST /api/admin/flow-configs` endpoint (or open a non-admin variant scoped to the user's team)

### 2. Conversational flow builder (LLM-assisted)
Highest-value idea. User describes the IVR they want — by voice or text — and the system drafts a `flow_configs.steps[]` JSON they can review before saving.
- **Input capture**: text field + mic button. Mic uses the browser's free `SpeechRecognition` API by default; optional Whisper upgrade for accuracy on accented English.
- **Intent → steps**: new lightweight LLM agent that converts a free-form description into a structured `steps[]` array compliant with the existing flow_configs schema (`id`, `purpose`, `max_words`). Reuse the Azure OpenAI client from `BaseAgent`.
- **Review UI**: show the generated steps in the same visual builder from item 1; user edits, saves.
- **Bonus**: also parse country/telco/language hints from the description so the rest of the campaign form prefills.
- Rough effort: 2–3 days end-to-end.

### 3. Script writer quality re-check
Goal: tighten the script writer so every variant is publishable without manual editing.
- Audit recent generated scripts to catalogue failure modes (off-brief CTAs, weak hooks, language drift, hallucinated features). Done as a one-off review.
- Tune the system prompt based on the audit (additional examples, stricter guardrails where weakest).
- Consider a self-critique step inside the writer (model critiques its own draft and revises) before handing off to the Eval Panel.
- Adaptive revision loop: instead of fixed `eval_feedback_rounds`, re-run until consensus score ≥ a threshold (e.g. 8/10) or max rounds hit.
- Track per-variant rejection reasons to feed back into prompt tuning over time.

---

## Reference

- ElevenLabs TTS body: `apply_text_normalization` = `auto` \| `on` \| `off` — `on` helps numbers/dates; avoid `optimize_streaming_latency=4` if you need normalizer on.
- Product upload accepts `.md`; expanding the text area reduces missed pricing/short codes before pipeline run.
