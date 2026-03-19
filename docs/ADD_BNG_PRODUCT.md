# BNG Products: add new product & edit content

## How to edit a product (e.g. AI personal assistant)

Product content can come from **two places**:

### 1. From the database (Supabase) — recommended for editing

If Supabase is configured and the `product_presets` table has rows, the app uses that data. To edit **AI personal assistant** (or any product):

1. Open your **Supabase** project → Table Editor → **product_presets**.
2. Find the row with `id` = `ai-personal-assistant` (or the product you want).
3. Edit:
   - **name** – Display name (e.g. "AI personal assistant").
   - **short_desc** – One-line description.
   - **full_description** – Long text with "Product Overview:", "Key Features:", etc. (see existing rows for format).
   - **icon** – One of: `Package`, `Sparkles`, `Radio`, `Shield`, `Mic2`, `Phone`, `Plane`, `Gamepad2`, `BookOpen`, `Moon`, `Cross`, `GraduationCap`.
   - **category** – One of: `ai`, `voice`, `connectivity`, `enterprise`, `entertainment`, `education`, `lifestyle`.
   - **display_order** – Number for ordering in lists.
4. Save. Refresh the app; the product page and home page will show the new content.

**If the table is empty:** Run the seed script once so the DB has default rows, then edit in Supabase:

```bash
python3 scripts/seed_product_presets.py
```

**If you had an old row with id `eva`:** You can update it to `ai-personal-assistant` in the DB (change the `id` column), or add a new row with id `ai-personal-assistant` and delete the `eva` row so the URL and data stay in sync.

**DB id for AI personal assistant:** The app loads the preset from DB when the row **id** is `ai-personal-assistant`, or `Personal Assistant`, or `personal assistant`, or `AI personal assistant`. So you can keep `id = 'Personal Assistant'` in Supabase and the product page will still use that row.

### Where each section on the product page comes from

| Section | Source | Where to edit |
|--------|--------|----------------|
| Title, short desc, overview | Preset (DB or fallback) | Supabase: `name`, `short_desc`, `full_description`. Or `ProductPresets.tsx` → `FALLBACK_RAW`. |
| **Metric cards** (95+ Languages, 4-6 weeks, etc.) | **Code only** | `frontend/src/app/product/[id]/page.tsx` → **`PRODUCT_STATS`** → key `"ai-personal-assistant"`. |
| **How it works** (numbered steps) | **Code only** | Same file → **`PRODUCT_FLOWS`** → key `"ai-personal-assistant"`. |
| **Key Features** (checkmark list) | Preset **full_description** | DB: `full_description` with line `Key Features:` and bullets `- ...`. Or `fullDescription` in `ProductPresets.tsx`. |

So: **cards** and **How it works** are only in code. **Key Features** and overview come from the preset text (DB or fallback).

### 2. From code (fallback when DB is not used)

If Supabase is not configured or returns no presets, the app uses the **fallback** list in code. To edit:

- **Name, short description, long description:**  
  `frontend/src/components/ProductPresets.tsx` → array `FALLBACK_RAW` → find the object with `id: "ai-personal-assistant"` and change `name`, `shortDesc`, `fullDescription`.
- **Metric cards and How it works steps:**
  `frontend/src/app/product/[id]/page.tsx` → **`PRODUCT_STATS`** (cards) and **`PRODUCT_FLOWS`** (steps) → key `"ai-personal-assistant"`.

After editing, rebuild/refresh the frontend.

---

# Adding a new product under BNG Products

To add a new product to the **BNG Products** dropdown in the sidebar (e.g. "My New Product"):

## 1. Sidebar entry

**File:** `frontend/src/components/Sidebar.tsx`

- Import an icon from `lucide-react` if you need a new one (e.g. `Star`).
- In `BNG_PRODUCT_LIST`, add:
  ```ts
  { id: "mynewproduct", label: "My New Product", icon: Star },
  ```
  Use a **lowercase, no-spaces** `id` (e.g. `mynewproduct`). This becomes the URL slug: `/product/mynewproduct`.

## 2. Product detail page (flow, stats, icon)

**File:** `frontend/src/app/product/[id]/page.tsx`

- **ICON_MAP:** Add `mynewproduct: <Star className="w-6 h-6" />` (use the same icon as in the sidebar).
- **PRODUCT_FLOWS:** Add a key `mynewproduct` with an array of `{ step, title, description }` for the "How It Works" section.
- **PRODUCT_STATS:** Add a key `mynewproduct` with an array of `{ label, value, icon }` for the stats cards.

## 3. Fallback preset (so "Product not found" doesn’t happen)

**File:** `frontend/src/components/ProductPresets.tsx`

- In `FALLBACK_RAW`, add an object with the **same `id`** as in the sidebar (`"mynewproduct"`):
  - `id`, `name`, `icon` (string, e.g. `"Star"`), `shortDesc`, `category`, `fullDescription`.

The product page loads presets from the API first; if none match the URL `id`, it uses this fallback. So the `id` in the sidebar, product page maps, and `FALLBACK_RAW` must all match.

## 4. Optional: Supabase

If you use the **product_presets** table in Supabase, add a row with the same logical id (e.g. set `id` to `mynewproduct` if your schema uses slug-style ids). The API will then return this preset and the product page will use it instead of the fallback.

---

**Summary:** Same `id` in Sidebar → product/[id] (ICON_MAP, PRODUCT_FLOWS, PRODUCT_STATS) → ProductPresets FALLBACK_RAW. Then the new product appears in the dropdown and its page loads without "Product not found".
