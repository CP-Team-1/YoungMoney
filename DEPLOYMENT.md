# Deployment

This covers running YoungMoney in production: `docker-compose.yml` +
`docker-compose.prod.yml`, TLS termination in nginx, and static files.
Local dev (`docker-compose.yml` alone) is unaffected by any of this.

## 1. Required environment variables (`server/.env`)

Copy `server/.env.example` to `server/.env` on the deploy host and set real
values — this file is gitignored and must never be committed. For a real
deploy, set these explicitly (don't leave the example defaults):

| Variable | Production value |
|---|---|
| `DJANGO_SECRET_KEY` | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`. Unique per environment, never reused from dev/CI. |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | Your real domain(s), e.g. `youngmoney.example.com`. Comma-separated if there's more than one (e.g. apex + `www`). |
| `DJANGO_USE_HTTPS` | `True` — only once nginx is actually terminating TLS (see §2). Turning this on before TLS exists will break the site (permanent HTTPS redirect with nothing listening on 443). |
| `POSTGRES_PASSWORD` | A strong, unique password — not the dev value. |
| `POSTGRES_DB`, `POSTGRES_USER` | Can keep the example values or change them; must match what the `db` service is initialized with. |
| `CORS_ALLOWED_ORIGINS` | Your real frontend origin, e.g. `https://youngmoney.example.com`. Remove the localhost entries. |
| `FRONTEND_URL` | Your real frontend origin (used to build links in outgoing email). |
| `GEMINI_API_KEY` | Production Gemini API key. |
| `CARDAPI_KEY` | Production CardAPI key. |
| `DJANGO_EMAIL_BACKEND` / `DJANGO_DEFAULT_FROM_EMAIL` | Point at a real SMTP backend once one is available — the default console backend just logs mail to container output. |

Treat every secret above as sensitive: keep `server/.env` off the host's
backup/log paths, restrict file permissions, and never echo it in CI logs.

## 2. TLS certificates

`docker-compose.prod.yml` mounts a cert/key pair into the nginx container
via two host paths, read from the shell environment (not `server/.env`,
since nginx doesn't read that file):

```bash
export SSL_CERT_PATH=/etc/letsencrypt/live/youngmoney.example.com/fullchain.pem
export SSL_KEY_PATH=/etc/letsencrypt/live/youngmoney.example.com/privkey.pem
```

Any cert works as long as those two paths point at a valid fullchain/privkey
pair (e.g. from `certbot`) — nginx doesn't care about the domain name itself,
so no domain is hardcoded in `nginx/default.prod.conf`. Renewing the
certificate (e.g. via a `certbot renew` cron job) just needs an nginx reload
(`docker compose exec nginx nginx -s reload`) afterward, no rebuild.

## 3. Running the production stack

```bash
cp server/.env.example server/.env   # then edit with real values, see §1
export SSL_CERT_PATH=... SSL_KEY_PATH=...   # see §2

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

This differs from plain `docker compose up` (local dev) in that it:

- Runs `collectstatic` then `migrate` then `gunicorn` (dev runs
  `manage.py runserver` for live reload) — see `server/Dockerfile` and
  `docker-compose.prod.yml`.
- Drops the `./server:/app` bind mount, so the container runs the image's
  baked-in code rather than the host checkout.
- Serves nginx over 443 with the TLS config in `nginx/default.prod.conf`,
  redirecting 80 → 443, instead of plain HTTP on 80.
- Restarts all services (`unless-stopped`) on failure/reboot.

## 4. Static files

`STATIC_ROOT` and whitenoise are configured in `server/youngmoney/settings.py`
so Django serves its own admin/DRF static assets directly (no separate nginx
static location needed) once `collectstatic` has run — which the prod
`command` above does automatically on every deploy.
