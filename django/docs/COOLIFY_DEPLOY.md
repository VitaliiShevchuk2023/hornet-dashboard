# Deploying hornet-django to Coolify (from scratch)

## 1. Get a server

Coolify runs on any Ubuntu 22.04/24.04 VPS you control (Coolify itself is
self-hosted, not a managed platform). Options that work well:

- Hetzner Cloud CX22 (~€4.5/mo, 2 vCPU / 4GB RAM) — cheapest reasonable option, EU-based (good for GDPR/NABU data)
- DigitalOcean Droplet (4GB RAM basic)
- Any VPS with a public IPv4 and root SSH access

Minimum spec for this project (Django + PostGIS + Redis + Celery worker + beat): **4GB RAM** recommended. 2GB will run but is tight once Celery is active.

Point a DNS A record (e.g. `hornet.yourdomain.org`) at the server's IP now — Coolify needs this for automatic HTTPS (Let's Encrypt) later.

## 2. Install Coolify

SSH into the fresh server as root, then:

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

This installs Docker + Coolify itself. Takes a few minutes. At the end it prints a URL like `http://<server-ip>:8000` — open that in a browser and create your admin account.

## 3. Connect your GitHub repo

In Coolify:

1. **Sources** → **+ Add** → GitHub → authorize the Coolify GitHub App, grant it access to `VitaliiShevchuk2023/hornet-dashboard`. The Django code lives in the `django/` subfolder of that same repo, alongside the Streamlit prototype at root — set the Base Directory when creating the app resource (step 5).
2. **Projects** → **+ New Project** → name it `hornet-dashboard`.

## 4. Add the database and Redis as Coolify resources

Inside the project:

1. **+ New Resource** → **Database** → **PostgreSQL** → but pick the **PostGIS** image variant (Coolify lets you override the Docker image — use `postgis/postgis:16-3.4`). Set DB name/user/password; Coolify generates a `POSTGRES_*` connection string you'll reuse below.
2. **+ New Resource** → **Database** → **Redis**. Default settings are fine.

Both get private networking automatically — your Django app reaches them by service name, not public IP.

## 5. Add the Django app as a resource

1. **+ New Resource** → **Application** → **Public/Private GitHub Repository** → select `VitaliiShevchuk2023/hornet-dashboard`, branch (e.g. `main`).
2. **Base Directory**: `/django` — **this is the one setting that's easy to miss.** Since the Django project lives in a subfolder alongside the Streamlit prototype (not at repo root), Coolify needs to be told where the build context is. Without this it'll try to build from repo root and fail to find the `Dockerfile`.
3. **Build Pack**: Dockerfile (Coolify looks for `Dockerfile` relative to the Base Directory above, so `django/Dockerfile`).
4. **Port**: `8000` (matches `EXPOSE 8000` / gunicorn bind).
5. **Domains**: set `hornet.yourdomain.org` — Coolify issues a Let's Encrypt cert automatically once DNS resolves.

Same applies to the Celery worker/beat resources in step 8 below — set **Base Directory** to `/django` on those too.

## 6. Environment variables

In the app's **Environment Variables** tab, add everything from `.env.example`, pointing `POSTGRES_*` and `REDIS_URL` at the Coolify-managed resources (Coolify shows you the internal hostnames/ports on each resource's page — typically the resource's service name, e.g. `POSTGRES_HOST=postgresql-database` or similar, copy exactly what Coolify shows).

Also add:
```
DJANGO_ALLOWED_HOSTS=hornet.yourdomain.org
DJANGO_CSRF_TRUSTED_ORIGINS=https://hornet.yourdomain.org
DJANGO_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(50))">
```

## 7. Run migrations (one-off)

After the first successful deploy, use Coolify's **Terminal** tab on the app resource (or `docker exec` via SSH) to run:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Then, once you have Theresa's finalized CSV:

```bash
python manage.py load_dashboard_csv /path/to/normalized_theresa_export.csv
```

## 8. Add Celery worker + beat as separate Coolify resources (Research track only)

Same GitHub repo, same Dockerfile, but override the **Start Command**:

- Resource `hornet-celery-worker` → Start Command: `celery -A config worker -l info`
- Resource `hornet-celery-beat` → Start Command: `celery -A config beat -l info`

Both need the same environment variables as the web app (`REDIS_URL`, `POSTGRES_*`). No public domain/port needed for either.

> This is exactly where the "no cron jobs" vs. "Research still needs it" distinction from the Aug 6 meeting materializes: only these two resources run continuously; the Dashboard web app itself is stateless and only reads what's already in Postgres.

## 9. Auto-deploy on push

Coolify's GitHub App sets up a webhook automatically — pushing to the tracked branch triggers a rebuild + redeploy of the `web` resource. Do the same for the worker/beat resources if you want them to redeploy together, or pin them to redeploy manually if you'd rather control Celery restarts separately (safer once real weekly pulls are running, to avoid interrupting an in-flight task).

## 10. Backups

Coolify's PostgreSQL resource has a **Backups** tab — enable scheduled backups to S3-compatible storage (Hetzner Object Storage works) before you load real NABU/GBIF data. Do this before step 7, not after.

## 11. Relationship to existing Azure infrastructure

**Decided: Coolify runs in parallel to the Azure infra (`rg-hornet-dashboard-prod`), not as a replacement.** They serve different things:

| Infra | Hosts | Notes |
|---|---|---|
| Azure (`rg-hornet-dashboard-prod`, westeurope) | Streamlit prototype — Container Apps, Container Registry, Blob Storage, Log Analytics | Stays as-is; keep it running for as long as the prototype is still in use for demos/internal review |
| Coolify (new VPS) | This Django + Leaflet app — both Dashboard and Research tracks | New, separate deployment target |

No shared runtime dependency between them — the Django app's Research track pulls GBIF data directly via `pygbif` in the Celery task, it does **not** read from the existing Azure Blob Storage CSVs. If that changes (e.g. reusing Azure Blob as a shared data lake for both apps), revisit this section and the Terraform/IaC scope with Jonas Stettner.

Worth a short note to Jonas and the team so nobody assumes the Azure resource group is being decommissioned once Coolify is live.

---

### Open items to resolve before this is production-ready

- `utils/naturgucker_loader.py` (German NABU schema → normalized CSV) still needs to be written and run *before* `load_dashboard_csv` — this scaffold assumes an already-normalized CSV as input.
- SBOM/security baseline (`SECURITY.md`, `cyclonedx-bom`, `pip-audit`) from the Streamlit repo should be ported over to this repo too.
