# Atelier Noir — API (demo instance)

A standalone copy of the **backend** (Django) and the **chatbot** (FastAPI +
OpenRouter) for the Atelier Noir formal-wear store. This repo is meant to be
deployed as its **own** pair of Vercel projects with its **own database**, so it
is fully independent of the original production deployment.

```
backend/             Django REST API (products, orders, chat proxy)
assistify_chatbot/   FastAPI AI concierge (OpenRouter tool-calling agent)
```

The demo **frontend** is a static build hosted separately (e.g. HostGator);
point it at this backend by editing its `config.js`.

---

## Deploy on Vercel (same account, two new projects)

### 1) Backend  →  new Vercel project, **Root Directory = `backend`**
Create a fresh Postgres DB first, then set these env vars (Production):

| Variable | Value |
|---|---|
| `DB_NAME` `DB_USER` `DB_PASSWORD` `DB_HOST` `DB_PORT` | the new database |
| `SECRET_KEY` | any long random string |
| `SEED_SECRET` | a strong secret (used once, then delete) |
| `MICROSERVICE_URL` | the chatbot URL from step 2 + `/chat` |
| `OPENROUTER_API_KEY` | (optional) only if needed server-side |

Deploy, then **seed the catalog** (migrate + 61 formal products w/ colors,
sizes, images, offers):

```bash
curl -X POST https://<NEW-BACKEND>.vercel.app/api/v1/products/admin/seed/ \
  -H "X-Seed-Secret: <SEED_SECRET>"
```

Expect `{"success": true, "product_count": 61}`. Then **remove `SEED_SECRET`**
and redeploy to close the endpoint.

### 2) Chatbot  →  new Vercel project, **Root Directory = `assistify_chatbot`**

| Variable | Value |
|---|---|
| `OPENROUTER_API_KEY` | your OpenRouter key |
| `BACKEND_URL` | the backend URL from step 1 (e.g. `https://<NEW-BACKEND>.vercel.app`) |

### 3) Wire them together
- Backend env `MICROSERVICE_URL` = `https://<NEW-CHATBOT>.vercel.app/chat`
- Chatbot env `BACKEND_URL` = `https://<NEW-BACKEND>.vercel.app`
- Demo frontend `config.js` → `window.__API_BASE__ = "https://<NEW-BACKEND>.vercel.app/api/v1";`

```
demo frontend ──▶ backend (this repo) ──MICROSERVICE_URL──▶ chatbot (this repo)
                      │                                          │
                  new database                              BACKEND_URL ──▶ backend
                                                            OPENROUTER_API_KEY
```

Product images are served by the static demo frontend at `/products/<slug>.jpg`;
this backend only stores those relative paths.
