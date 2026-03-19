# Configured voices & accents

This is the **in-repo** inventory. **ElevenLabs** also loads **your account voices** via API (`/v2/voices`) and **shared library** voices via `/v1/shared-voices` (accent/search) at runtime—those are not duplicated here.

---

## Summary: African region / accent

| Engine      | Native African-accent voices in our config? | Notes |
|-------------|---------------------------------------------|--------|
| **ElevenLabs** | **No** (in curated premade list)            | Curated list only has American, British, Neutral, Transatlantic, Australian. We *target* African markets via `best_for_regions` (e.g. Lily, Daniel for east_africa) but the **accent label** is not “African”. African-accent discovery happens at runtime via **shared library** (`GET /v1/shared-voices` with `accent=african`, etc.) when the API key has access. |
| **Edge-TTS**   | **Yes**                                    | Explicit African locales: **en-NG** (Nigeria), **en-KE** (Kenya), **en-ZA** (South Africa), **en-GH** (Ghana), **en-TZ** (Tanzania), **sw-KE** (Swahili), **zu-ZA** (Zulu), **af-ZA** (Afrikaans), **am-ET** (Amharic), **so-SO** (Somali). Real neural voices per region. |
| **Murf**      | **Country mapping only**                   | We map Nigeria, Kenya, Tanzania, South Africa, Ghana, Ethiopia, etc. to Murf **country** config, but the **voice_id** used is typically `en-US-samantha` or `en-IN-arohi` — i.e. US/Indian English, not native African-accent voices in our code. |

So: for **built-in African-accent voices** in the repo, **Edge-TTS has them**; ElevenLabs relies on shared library or your account; Murf gives African *targeting* but not African-accent voice IDs in the current tables.

---

## 1. ElevenLabs — curated premade list (Voice Selector fallback + pool fallbacks)

**File:** `backend/agents/voice_selector.py` → `_CURATED_ELEVENLABS_VOICES`

| Name     | voice_id              | Accent        | Gender | best_for_regions (summary)      |
|----------|------------------------|---------------|--------|----------------------------------|
| Sarah    | EXAVITQu4vr4xnSDxMaL   | American      | female | americas, europe, general        |
| Rachel   | 21m00Tcm4TlvDq8ikWAM   | American      | female | americas, general                |
| Charlotte| XB0fDUnXU5powFXDhCwa   | Neutral       | female | south_asia, middle_east, general |
| Lily     | pFZP5JQG7iQjIQuC4Bku   | British       | female | east_africa, southern_africa, south_asia |
| Aria     | 9BWtsMINqrJLrRacOk9x   | American      | female | general, south_asia, west_africa |
| Dorothy  | ThT5KcBeYPX3keUQqHPh   | British       | female | east_africa, west_africa, south_asia |
| Alice    | Xb7hH8MSUJpSbSDYk0k2   | British       | female | east_africa, south_asia, middle_east |
| Freya    | jsCqWAovK2LkecY7zXl4   | American      | female | americas, europe                 |
| Jessica  | cgSgspJ2msm6clMCkdW9   | American      | female | americas, latam, general         |
| Gigi     | jBpfuIE2acCO8z3wKNLl   | American      | female | apac, latam, general             |
| Daniel   | onwK4e9ZLuTAKqWW03F9   | British       | male   | east_africa, southern_africa, south_asia |
| George   | JBFqnCBsd6RMkjVDRZzb   | British       | male   | east_africa, west_africa, south_asia |
| Eric     | cjVigY5qzO86Huf0OWal   | American      | male   | general, south_asia, west_africa |
| Liam     | TX3LPaxmHKxFdv7VOQHJ   | American      | male   | general, middle_east, latam      |
| Adam     | pNInz6obpgDQGcFmaJgB   | American      | male   | americas, europe                 |
| Brian    | nPczCjzI2devNBz1zQrb   | American      | male   | americas, general                |
| Callum   | N2lVS1w4EtoT3dr4eOWO   | Transatlantic | male   | general, apac, middle_east       |
| Charlie  | IKne3meq5aSn9XLyUdCD   | Australian    | male   | apac, general                    |

**Runtime:** Voice Selector calls ElevenLabs **`GET /v2/voices`** when the API key has **`voices_read`**. If the key is **TTS-only** (no `voices_read`), we skip the API and use **only** the curated list above—so the app works with keys that have text-to-speech but not voice-list permission (e.g. keys provided by a third party). The table above is also the **fallback** when the voices API fails or returns 401.

**Shared library:** `audio_producer._build_elevenlabs_voice_pool` queries **`GET /v1/shared-voices`** with `accent` / `search` (e.g. african, nigerian, kenyan, ethiopian…) so **additional accents** appear in preview pools when the API returns them.

---

## 2. Edge-TTS — pools (locale = accent/region)

**File:** `backend/agents/audio_producer.py` → `EDGE_VOICE_POOL`

Each locale is a **Microsoft neural voice**; the locale code implies region/accent.

| Locale pool | Voices (label) |
|-------------|----------------|
| **en-IN**   | Neerja, Prabhat, Neerja Expressive |
| **hi-IN**   | Swara, Madhur |
| **ta-IN**   | Pallavi, Valluvar |
| **te-IN**   | Shruti, Mohan |
| **bn-IN**   | Tanishaa, Bashkar |
| **en-NG**   | Ezinne, Abeo (Nigeria English) |
| **en-KE**   | Asilia, Chilemba (Kenya English) |
| **en-US**   | Aria, Guy, Jenny |
| **en-GB**   | Sonia, Ryan, Libby |
| **fr-FR**   | Denise, Henri, Eloise |
| **pt-BR**   | Francisca, Antonio |
| **ur-PK**   | Uzma, Asad |
| **id-ID**   | Gadis, Ardi |
| **sw-KE**   | Zuri, Rafiki (Swahili) |
| **en-ZA**   | Leah, Luke (South Africa English) |
| **en-GH**   | Esi, Ekua (Ghana English) |
| **en-TZ**   | Imani, Elimu (Tanzania English) |
| **zu-ZA**   | Thando, Themba (Zulu) |
| **af-ZA**   | Adri, Willem (Afrikaans) |
| **am-ET**   | Mekdes, Ameha (Amharic) |
| **so-SO**   | Ubax, Muuse (Somali) |
| **fil-PH**  | Blessica, Angelo |
| **ar-SA** / **ar-EG** | Zariyah, Hamed, Salma, Shakir |

Country → locale routing is in **`COUNTRY_LOCALE`** and **`LANGUAGE_TO_LOCALE`** in the same file.

---

## 3. Murf AI — by language & by country

**File:** `backend/agents/audio_producer.py` → `MURF_VOICE_MAP`, `MURF_VOICE_POOL`, `MURF_COUNTRY_VOICE`

### By language (MURF_VOICE_MAP / MURF_VOICE_POOL)

| Language key   | Typical voice_id   | Locale | Style        |
|----------------|--------------------|--------|--------------|
| hindi          | hi-IN-ayushi       | hi-IN  | Conversational |
| hinglish       | hi-IN-ayushi       | hi-IN  | Conversational |
| tamil          | ta-IN-iniya        | ta-IN  | Conversational |
| telugu         | en-IN-arohi        | te-IN  | Promo        |
| bengali        | bn-IN-anwesha      | bn-IN  | Conversational |
| kannada        | en-UK-hazel        | kn-IN  | Conversational |
| english        | en-IN-arohi        | en-IN  | Promo        |
| french         | fr-FR-adélie       | fr-FR  | Narration    |
| portuguese     | pt-BR-isadora      | pt-BR  | Conversational |
| …              | …                  | …      | …            |

### By country (MURF_COUNTRY_VOICE)

| Country        | voice_id        | Locale | Style     |
|----------------|-----------------|--------|-----------|
| India          | en-IN-arohi     | en-IN  | Promo     |
| Nigeria/Kenya/Tanzania/South Africa/Ghana/Ethiopia | en-US-samantha | en-US | Promo |
| Cameroon/Senegal/Congo (DRC) | fr-FR-adélie | fr-FR | Narration |
| Mozambique     | pt-BR-isadora   | pt-BR  | Conversational |
| Bangladesh     | bn-IN-anwesha   | bn-IN  | Conversational |
| Pakistan       | en-US-samantha  | en-US  | Promo     |
| Indonesia      | en-US-zion      | id-ID  | Conversational |
| Philippines    | en-IN-arohi     | en-IN  | Promo     |

---

## 4. Where pool order is decided (ElevenLabs)

**File:** `backend/agents/audio_producer.py` → `_build_elevenlabs_voice_pool`

1. LLM primary + alternative `voice_id`s from Voice Selector  
2. Your library voices from **`/v2/voices`** (professional/high_quality/cloned) filtered by **preferred_accents** for the region  
3. **Shared voices** from **`/v1/shared-voices`** (accent + search)  
4. Curated premade IDs (same IDs as table in §1), shuffled per session  

---

## 5. Quick file map

| What you want              | Where to look |
|----------------------------|----------------|
| ElevenLabs premade + accents | `backend/agents/voice_selector.py` → `_CURATED_ELEVENLABS_VOICES` |
| Edge pools by locale       | `backend/agents/audio_producer.py` → `EDGE_VOICE_POOL` |
| Murf by language/country   | `audio_producer.py` → `MURF_VOICE_MAP`, `MURF_COUNTRY_VOICE`, `MURF_VOICE_POOL` |
| African accent search terms | `audio_producer.py` → `_build_elevenlabs_voice_pool` → `_shared_accent_queries` |
| Country → Edge locale      | `audio_producer.py` → `COUNTRY_LOCALE`, `LANGUAGE_TO_LOCALE` |

---

## 6. Listing every voice in your ElevenLabs account (API)

With your API key:

```bash
curl -s "https://api.elevenlabs.io/v2/voices?page_size=100" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" | jq '.voices[] | {voice_id, name, labels}'
```

Shared library sample (African filter):

```bash
curl -s "https://api.elevenlabs.io/v1/shared-voices?page_size=30&accent=african&language=en" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" | jq '.voices[] | {voice_id, name, accent, gender}'
```

This doc is **static**; your account and the shared library change over time—use the API to export the live list when needed.
