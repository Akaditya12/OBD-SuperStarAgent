# Flow config: Vodacom Tanzania MagicVoice

## What was added

A **3-step flow** for Vodacom Tanzania MagicVoice (Swahili campaigns), aligned with your design:

1. **welcome** – Warm welcome and MagicVoice intro. **No CTA or shortcode** so the user is not overloaded; behavior is easier to predict.
2. **subscription_doubleconsent** – Subscription options, price point, and double consent (e.g. Press 1 for X, Press 2 for Y).
3. **thanks** – Thank you, confirm activation, **CTA and shortcode** (e.g. dial X, remember X).

Same pattern as BTC Christianity: CTA/shortcode only in the final step.

## How to seed (Supabase)

From project root, with `.env` containing `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`:

```bash
python3 scripts/seed_flow_configs.py
```

This **upserts** both BTC Christianity and Vodacom Tanzania MagicVoice (on `account_key` + `service_key`). Existing rows are updated; new ones inserted.

## How to generate a Swahili campaign

1. **Product** – Use a product that fits MagicVoice (e.g. paste a short MagicVoice brief, or use a preset).
2. **Country** – **Tanzania**.
3. **Telco** – **Vodacom Tanzania** (must match the flow’s `account_key` so the flow dropdown appears).
4. **Language** – **Swahili** (or the code your app uses, e.g. `sw`).
5. **Flow** – In the flow dropdown, select **“Vodacom Tanzania MagicVoice 3-step”**.
6. Run the pipeline; scripts and audio will be generated per step (welcome → subscription_doubleconsent → thanks) in Swahili.

## Rollback (if needed)

- **Remove only Vodacom flow:** In Supabase → Table Editor → **flow_configs** → delete the row with `account_key = 'Vodacom Tanzania'` and `service_key = 'MagicVoice'`. No code change.
- **Revert seed script:** In `scripts/seed_flow_configs.py`, remove the Vodacom Tanzania entry from the `rows` list and the `VODACOM_TANZANIA_MAGICVOICE_STEPS` definition; run the seed again if you want to keep only BTC in the DB.
- **Current app behavior** is unchanged; this is additive (one new flow_config row). If you don’t select “Vodacom Tanzania” as telco or don’t pick this flow, nothing different runs.

## Step IDs for audio

Audio files will be named with these step IDs:

- `voice1_step_welcome`
- `voice1_step_subscription_doubleconsent`
- `voice1_step_thanks`

(and similarly for other variants/voices). The script writer and audio producer already support arbitrary step IDs from `flow_config.steps`.
