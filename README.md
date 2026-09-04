# GeoShield AI — Landslide Early Warning & Public Safety Portal

SIH26001 — full working prototype: FastAPI + RandomForest/SHAP backend,
React + Leaflet frontend with a Citizen Portal and an Officer Console.

```
geoshield-ai/
  backend/     FastAPI API, ML model, sensor simulator  (see backend/README.md)
  frontend/    React + Vite + Tailwind + Leaflet — two apps, one codebase:
                 /          Citizen Portal (map, alerts, SOS, 3 languages)
                 /officer   Officer Console (dashboard, broadcast, SOS queue)
  docker-compose.yml   run everything locally with one command
  render.yaml           deploy everything to Render with one click
```

## Run everything locally

**Option A — Docker Compose (simplest):**
```bash
docker compose up --build
```
Then open:
- Citizen Portal: http://localhost:5173
- Officer Console: http://localhost:5173/officer
- API docs: http://localhost:8000/docs

**Option B — manual (three terminals):**
```bash
# 1. backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. sensor simulator (fake IoT data)
cd backend
python simulate_sensors.py

# 3. frontend
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Deploying both together

**Render (recommended — one blueprint, three services, all free-tier):**

1. Push this whole `geoshield-ai/` folder to a GitHub repo.
2. In Render: **New → Blueprint**, point it at the repo. Render reads
   `render.yaml` and creates three services:
   - `geoshield-api` — the FastAPI backend (Docker)
   - `geoshield-sensor-simulator` — background worker feeding fake telemetry
   - `geoshield-frontend` — the static React build
3. After the first deploy, Render gives `geoshield-api` a URL like
   `https://geoshield-api.onrender.com`. Copy it into:
   - `render.yaml` → `geoshield-sensor-simulator` → `API_BASE`
   - `render.yaml` → `geoshield-frontend` → `VITE_API_BASE`
   Commit and push — Render redeploys automatically.
4. (Optional, for data to survive restarts) Add a Render PostgreSQL
   instance and set `DATABASE_URL` on `geoshield-api`.
5. Open the `geoshield-frontend` URL — that's your live demo link for
   judges. Officer console is `<that-url>/officer`.

**Vercel/Netlify + Render split (if you prefer separate providers):**
- Frontend → Vercel or Netlify: import the repo, set root directory to
  `frontend/`, build command `npm run build`, output `dist`, and add env var
  `VITE_API_BASE=https://<your-render-api-url>`.
- Backend + simulator → Render, same as steps 1–4 above but skip the
  `geoshield-frontend` service in `render.yaml` (or just ignore it).
- **Important:** whichever way you split it, open `backend/app/main.py` and
  change `allow_origins=["*"]` to your real frontend URL before treating
  this as anything beyond a demo — wide-open CORS is fine for a hackathon,
  not for anything after.

## What to say to judges about the "IoT" layer

There's no physical sensor hardware here — `simulate_sensors.py` plays that
role, posting telemetry shaped by real rainfall/pore-pressure trigger
thresholds (cited in your PPT: Sikkim SDMA, Harilal et al.). Say this
plainly when demoing: the ingestion API, risk model, SHAP explainability,
alerting, and both UIs are the real, working parts of the system — the
sensor layer is deliberately simulated to prove the software end-to-end
without needing field hardware for a hackathon.

## What's left to build

- Safe alternate-route suggestion (OSRM/GraphHopper call filtering out
  Danger-zone sensors) — biggest remaining differentiator from your PPT.
- Role-based login for the Officer Console (currently open — fine for a
  demo, not for production).
- PDF/CSV incident export from the officer console.
- Swap SQLite → Postgres for anything beyond a demo.
