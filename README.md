# Nassau Candy Distributor — Shipping Route Efficiency Dashboard

A Streamlit web application implementing the project's required dashboard modules.

## Files
- `app.py` — the Streamlit application (run this)
- `nassau_logic.py` — all cleaning, feature engineering, and analysis logic (imported by `app.py`)
- `Nassau_Candy_Distributor.csv` — the raw source dataset
- `requirements.txt` — Python dependencies

## How to run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## What it does

On startup, the app runs the full cleaning + feature engineering pipeline directly
on the raw CSV (cached so it only runs once per session) — there are no precomputed
intermediate files to keep in sync. This includes:

- Excluding 200 out-of-scope Canadian records (US-only project scope)
- Reconstructing **Shipping Lead Time** from the raw Order/Ship Date fields, which
  contain a systematic multi-year offset artifact (see `data_quality_and_cleaning_decisions.md`
  for the full diagnostic writeup)
- Joining each order to its source Factory via the Product Name lookup, and to
  Factory coordinates for mapping
- Computing the Route Efficiency Score, Delay Frequency, and Geographic Bottleneck flags

## Dashboard modules

1. **Route Efficiency Overview** — average lead time by route, route performance leaderboard
   with the Route Efficiency Score
2. **Geographic Shipping Map** — US choropleth of lead time by state, regional bottleneck
   flags (High Lead Time / Congestion)
3. **Ship Mode Comparison** — lead time by ship mode, descriptive cost-time tradeoff,
   delay frequency by mode
4. **Route Drill-Down** — state-level performance summary, factory breakdown, and an
   order-level shipment timeline scatter plot

## Global filters (sidebar)
- Order date range
- Region (multi-select)
- State/Province (multi-select, narrows based on selected regions)
- Ship Mode (multi-select)
- Lead-time threshold slider — drives the Delay Frequency KPI everywhere it appears.
  Default value is the 75th percentile of all shipment lead times (~5 days).

## Known data limitations (disclosed, not hidden)
- **Low-volume routes** (fewer than 5 shipments) are flagged, not excluded, from the
  Route Efficiency leaderboard — their scores should be read with caution.
- **Delay Frequency** uses a single global threshold across all ship modes, so it
  largely reflects each mode's typical speed tier rather than true within-mode anomalies.
- **Cost/Sales/Gross Profit** reflect product cost-to-manufacture and sale price, not
  shipping/freight cost — no freight-cost field exists in the source data.
