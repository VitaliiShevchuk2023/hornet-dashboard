# NABU Hornet Dashboard — Django + Leaflet (migration scaffold)

> Lives at `django/` inside `VitaliiShevchuk2023/hornet-dashboard`, alongside
> the Streamlit prototype at repo root. All commands below assume you're
> `cd django` first. Coolify's app resource is configured with
> **Base Directory = `/django`** — see `docs/COOLIFY_DEPLOY.md`.

Migration target for the Streamlit prototype, covering **both** tracks:

| App | Track | Data source | Scheduling |
|---|---|---|---|
| `apps.dashboard` | Team Dashboard (public) | One-off import of Theresa's finalized CSV | **None** — `manage.py load_dashboard_csv`, run manually after handover |
| `apps.research` | Team Research (Q1–Q6) | Continuous GBIF pull via `pygbif` | Celery beat, weekly |

## Local dev

```bash
cp .env.example .env   # edit values
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

App: http://localhost:8000 · Research: http://localhost:8000/research/ · Admin: http://localhost:8000/admin/

## What's ported from the Streamlit prototype

- `utils/gbif_loader.py` GADM-parsing logic → `apps/research/tasks.py::_safe_gadm`
- `gdown`/Google Drive fallback → **removed entirely** (was dead code + CVE liability, per earlier prototype review)
- Q3/Q4 locality-keyword habitat & protected-area proxies → `apps/research/views.py` (same technical debt carried over — real spatial join with WDPA/habitat polygons is still a TODO)
- `pages/4_Urban_Rural.py` (was an empty placeholder) → `apps/research/views.py::urban_rural` (still a placeholder, needs real Q5 analysis)
- Photo-verified filter (Theresa's "safe way" recommendation) → `Observation.photo_verified` / `GbifObservation.photo_verified`, defaults to **on** in the public Dashboard API

## What's NOT yet ported

- `utils/naturgucker_loader.py` — NABU's German-schema Excel → normalized CSV adapter. `load_dashboard_csv` currently expects already-normalized input.
- Q6 Open-Meteo ERA5 climate integration (`pages/6_Climate.py`) — low priority per Theresa, template is a stub.
- SBOM / `SECURITY.md` baseline from the Streamlit repo.

## Deployment

See [`docs/COOLIFY_DEPLOY.md`](docs/COOLIFY_DEPLOY.md) for a full from-scratch Coolify setup (server → Coolify install → GitHub connect → PostGIS + Redis resources → app + Celery worker/beat resources → env vars → migrations → backups).
