# GeoShield AI — Backend (Milestone 1)

This is the first piece of the build: the FastAPI service, the RandomForest
risk-scoring model + SHAP explainability, and a sensor simulator standing in
for real IoT hardware. Frontend (Citizen Portal + Officer Console) is next.

## What's here

```
backend/
  app/
    main.py          FastAPI app: sensors, readings, alerts, SOS, WebSocket
    models.py         SQLAlchemy tables
    schemas.py         Pydantic request/response models
    risk_engine.py     Loads model.pkl + explainer.pkl, scores a reading
    ws_manager.py       Live broadcast to connected clients
    database.py         SQLite (swap for Postgres via DATABASE_URL env var)
  ml/
    generate_dataset.py  Builds a synthetic-but-threshold-realistic training set
    train_model.py       Trains RandomForest + SHAP TreeExplainer
    model.pkl / explainer.pkl / features.pkl   (already trained, committed)
  data/
    landslide_training_data.csv
  simulate_sensors.py   Seeds 5 NER-corridor sensors, posts fake telemetry on a loop
  requirements.txt
```

## Run it locally

```bash
cd backend
pip install -r requirements.txt

# model.pkl is already trained and included — only re-run these if you
# change the feature set or want a different synthetic dataset:
#   python ml/generate_dataset.py
#   python ml/train_model.py

uvicorn app.main:app --reload --port 8000
```

In a second terminal, start the simulator so there's live data to look at:

```bash
python simulate_sensors.py            # loops forever, posts every 5s
# or
python simulate_sensors.py --once     # single round, good for testing
```

Check it's alive:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/readings/latest      # what the map will render
```

Interactive API docs (Swagger) are auto-generated at `http://localhost:8000/docs`
— useful for testing endpoints before the frontend exists, and worth showing
to judges as evidence of a real API contract.

## Key design notes (for your pitch / SIH report)

- **The IoT layer is simulated** (`simulate_sensors.py`) using threshold ranges
  drawn from the rainfall/pore-pressure trigger literature you cited (Sikkim
  SDMA / Harilal et al.). Say this openly — judges respect disclosed
  simulation far more than an implied "real sensors" claim you can't back up.
- **Risk classes are quantile-balanced** (55% Safe / 30% Watch / 10% Warning /
  5% Danger) so the demo can reliably show all four states, including a
  believable rare Danger event, instead of a model that only ever says "Safe."
- **SHAP runs per-prediction**, not just globally — `top_factors` in every
  `/readings` response is what should power the "why this alert" panel in
  both the citizen and officer UI.
- **Auto-alerting**: any Warning/Danger reading creates an Alert row and
  broadcasts it over WebSocket without an officer needing to act — this is
  what makes the system "predictive, not just reactive," per your PPT's
  core pitch.

## Next steps (not yet built)

1. React + Vite + TS + Tailwind + Leaflet frontend — Citizen Portal (map,
   alert feed, SOS button) and Officer Console (thresholds, broadcast,
   incident log), both consuming this API and the `/ws` WebSocket.
2. Route-avoidance (call OSRM/GraphHopper, filter through Danger-zone sensors).
3. Multilingual message strings (Hindi/Assamese) — `Alert.message_hi` /
   `message_as` fields already exist; only the content needs filling in.
4. Swap `DATABASE_URL` to Postgres and lock down CORS before deploying for real.

## Deployment (once you're ready)

**Render (recommended — supports WebSockets on the free tier):**
1. Push this repo to GitHub.
2. New Web Service on Render → point at `backend/`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add a Render PostgreSQL instance and set `DATABASE_URL` if you want
   persistence beyond a single container restart (SQLite resets on redeploy).
6. Run `simulate_sensors.py` as a Render **Background Worker** (separate
   service, same repo) with `API_BASE` set to your deployed backend URL —
   this keeps your live demo populated with data even when your laptop is off.

**Railway** works the same way and is equally free-tier friendly if you
prefer it over Render.
