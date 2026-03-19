# RCA: Translation failed at Results step

## Symptom

At the **Results** step (after scripts and hook previews are ready), clicking **"Translate to English"** on a script variant (e.g. Amharic) showed a red toast: **"Translation failed. Please try again."** The feature had worked before.

## Root cause (summary)

Translation uses the same Azure OpenAI LLM as the rest of the app. Failures were caused by one or more of:

1. **Azure content filter** – The translate request sends the script (including tags like `[warm]`, `[cheerfully]` and transliterated text) as user content. Azure’s content policy can flag this as instruction-like or “jailbreak” and return 400, which was then surfaced as a generic 500 and "Translation failed."
2. **Prompt framing** – The user message was phrased as “Translate this to English: …” so the model (or the filter) could treat the script as instructions rather than as content to translate.
3. **No specific error handling** – All exceptions (ValueError for content filter, `JSONDecodeError` for malformed LLM output, timeouts) were caught as a single `Exception` and returned the same 500 message, so the real cause was hard to see.
4. **Frontend ignored API error body** – The UI always showed “Translation failed. Please try again.” even when the API returned a more specific message (e.g. content policy, timeout).

## Changes made

### Backend (`backend/main.py`)

- **Explicit support for all configured languages**  
  The translate system prompt now explicitly lists all supported languages (Amharic, Oromo, Swahili, Hindi, Tamil, Arabic, French, etc., including transliterated forms) so the model reliably translates any of them to English.

- **Amharic-first minimal prompt**  
  When `source_language` is Amharic (or contains "amharic"), the first request uses a minimal user prompt (no "Source language hint" line) to reduce the chance of Azure content filter triggering on transliterated Amharic.

- **Retry on content filter (503)**  
  If the first attempt is blocked by Azure's content policy (ValueError), we retry once with a simplified prompt: "Translate to English:\n\n" + text with all `[warm]`, `[urgent]`, etc. tags stripped. If the retry succeeds, translation is returned; if not, we still return 503 with the same user message.

- **Prompt reframing**  
  - System prompt now states that the user’s message is **script content to translate**, not instructions.  
  - User prompt uses a clear delimiter: `"Translate the following script to English.\n\nTEXT:\n\n" + text` to reduce content-filter false positives.

- **Input length cap**  
  - Script text is limited to **8000 characters** (`TRANSLATE_MAX_TEXT_CHARS`). Longer text is truncated with a note to avoid timeouts and oversized requests.

- **Explicit error handling**  
  - **ValueError** (e.g. Azure content filter) → **503** with:  
    `"Translation is temporarily unavailable. Try again or shorten the script."`  
  - **TimeoutError / asyncio.TimeoutError** → **504** with:  
    `"Translation timed out. Please try again."`  
  - **json.JSONDecodeError** (invalid JSON from LLM) → **500** with:  
    `"Translation failed. Please try again."`  
  - Other **Exception** → **500** with the same user-facing message; full traceback is logged.

- **Timeout**  
  - `call_llm` for translation now uses **90s** timeout so long scripts don’t hang indefinitely.

### Frontend

- **Results page** (`frontend/src/app/page.tsx`), **ScriptReview** (`frontend/src/components/ScriptReview.tsx`), and **Dashboard** (`frontend/src/app/dashboard/page.tsx`):  
  - On translate API failure, the response body is parsed and the **`error`** field from the API is shown in the toast (or inline message in ScriptReview) instead of always showing "Translation failed. Please try again."

## How to verify

1. Run a campaign to the Results step with a non-English script (e.g. Amharic).
2. Click **"Translate to English"** on a variant.
3. Translation should succeed and show the English text.
4. If it fails (e.g. content filter), the toast should show the API message (e.g. “Translation is temporarily unavailable. Try again or shorten the script.”).
5. Check `backend.log` for `Translation failed`, `Translation blocked`, or `Translation JSON parse failed` to see the exact cause if needed.

## If translation still fails

- **503 / “temporarily unavailable”** – Content policy likely; try again, shorten the script, or remove very long tags/segments.  
- **504 / “timed out”** – Script may be too long; use a shorter segment or try again.  
- **500 / “Please try again”** – Check backend logs for `Translation failed` or `Translation JSON parse failed`; may be LLM output format or a transient error.
