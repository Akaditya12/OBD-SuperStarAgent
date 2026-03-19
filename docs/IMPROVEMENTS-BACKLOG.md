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

## Reference

- ElevenLabs TTS body: `apply_text_normalization` = `auto` \| `on` \| `off` — `on` helps numbers/dates; avoid `optimize_streaming_latency=4` if you need normalizer on.
- Product upload accepts `.md`; expanding the text area reduces missed pricing/short codes before pipeline run.
