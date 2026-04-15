## NABU Hornet Dashboard — Streamlit Prototype

**Project:** CorrelAid × NABU (Naturschutzbund Deutschland)
**Purpose:** Exploratory prototype for analyzing the spread of *Vespa crabro* (European hornet) and *Vespa velutina* (Asian hornet) using GBIF occurrence data.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)


### Architecture Overview

The app is structured as a multi-page Streamlit application with a shared data loading utility:

```
streamlit_app.py          # Main dashboard / landing page
utils/gbif_loader.py      # Shared data loading & caching logic
pages/
  1_Overview.py           # Q1 — Species displacement & overlap map
  2_Displacement.py       # Q2 — European hornet geographic distribution
  3_Distribution.py       # Q5 — Synanthropic behavior (urban vs. rural)
  4_Habitat.py            # Q3 — Habitat type analysis
  4_Urban_Rural.py        # (empty / placeholder)
  5_Protected_Areas.py    # Q4 — Presence in protected areas
  6_Climate.py            # Q6 — Climate & weather influence
```

---

### Data Layer (`utils/gbif_loader.py`)

- Loads occurrence data for both species via **pygbif** (GBIF API)
- For Germany (`DE`), prioritizes **Google Drive CSV cache** (pre-downloaded via `download_gbif.py`) to avoid repeated API calls; falls back to live GBIF API for other countries
- All data is cached with `@st.cache_data` (TTL: 1h for API calls, 24h for Drive downloads)
- Cleans and normalizes fields: coordinates, `year`/`month` from `eventDate`, GADM administrative levels (`bundesland`, `landkreis`), species label and color
- Exposes `SPECIES`, `COLORS`, `load_both()`, and `load_observations()` to all pages

---

### Pages & Research Questions

| Page | Research Question | Key Visualizations |
|---|---|---|
| **Main** | Overview | Timeline (line chart), scatter map |
| **Q1 Overview** | Is the European hornet being displaced? | Overlap scatter map, bar chart by Bundesland |
| **Q2 Displacement** | European hornet distribution in Germany | Latitude/longitude histograms, density heatmap |
| **Q3 Habitat** | Habitat type correlation | Keyword-based locality classification, grouped bar + pie chart, monthly seasonality |
| **Q4 Protected Areas** | More sightings in Natura 2000 / national parks? | Keyword-based protected area flag, grouped bar + pie chart |
| **Q5 Distribution** | Is Asian hornet synanthropic? | Regional bar chart, raw data table, debug mode |
| **Q6 Climate** | Weather influence on spread | Latitude-based climate zones, seasonal line chart, Open-Meteo January temperature bar chart |

---

### Sidebar Controls

All pages share consistent sidebar filters:
- **Country** — `DE`, `FR`, `BE`, `NL`, `AT`, `CH`
- **Max records per species** — slider (100–1000)
- **Year range** — slider (2000–2025)

---

### Notable Design Decisions

- **Proxy-based habitat analysis** — both habitat type (`Q3`) and protected area status (`Q4`) are inferred from free-text `locality` field using keyword matching (e.g., `"wald"`, `"naturschutz"`). This is a pragmatic workaround pending proper spatial joins with Natura 2000 / WDPA polygon data.
- **Synanthropic bias warning** — `Q5` explicitly flags the citizen science detection bias (urban areas are over-represented due to more observers).
- **External climate data** — `Q6` fetches real historical temperature data from **Open-Meteo ERA5** API for 6 German cities to proxy winter severity.
- **Offline-first for Germany** — `download_gbif.py` pre-downloads full GBIF datasets per year (up to 20,000 records/year) to avoid rate limits during live demos.

---

### Known Limitations / Next Steps

- `pages/4_Urban_Rural.py` is currently empty — urban/rural analysis not yet implemented
- Habitat and protected area classification relies on locality text keywords, not actual spatial boundaries
- No statistical testing yet (correlation, significance)
- Designed as a **Streamlit prototype** — the production target is a **Django + HTMX** dashboard with PostgreSQL/PostGIS backend









### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```
