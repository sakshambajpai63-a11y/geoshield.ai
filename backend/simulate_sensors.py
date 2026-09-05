"""
Stand-in for real IoT hardware. Run this alongside the API server so the
map/alerts/officer console have live data to react to during your demo.

Usage:
  python simulate_sensors.py             # seeds 6 NER-corridor sensors, then loops forever
  python simulate_sensors.py --once      # single pass (useful for testing)

Env:
  API_BASE (default http://localhost:8000)
  DATAGOVIN_API_KEY  -> your data.gov.in personal key. Falls back to the
                        public sample key (10 records/request, fine for
                        this since we only fetch ~117 rows per subdivision
                        once at startup and cache them).
"""
import argparse
import os
import random
import time
from datetime import datetime

import requests

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
DATAGOVIN_API_KEY = os.getenv(
    "DATAGOVIN_API_KEY",
    "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b",  # public sample key
)
RAINFALL_RESOURCE_ID = "8e0bd482-4aba-4d99-9cb9-ff124f6f1c2f"

# Rough points along real NER landslide-prone corridors mentioned in the PPT
SEED_SENSORS = [
    {"name": "NH-10 KM 42", "corridor": "NH-10 Sikkim", "latitude": 27.0410, "longitude": 88.2661},
    {"name": "NH-10 KM 58", "corridor": "NH-10 Sikkim", "latitude": 27.0710, "longitude": 88.2890},
    {"name": "Gangtok Bypass", "corridor": "Gangtok", "latitude": 27.3389, "longitude": 88.6065},
    {"name": "Kohima Slope Watch", "corridor": "NH-29 Nagaland", "latitude": 25.6751, "longitude": 94.1086},
    {"name": "Aizawl Ridge", "corridor": "NH-54 Mizoram", "latitude": 23.7271, "longitude": 92.7176},
    # New: Assam, matching the Karbi Anglong / Cachar landslide zones from the PPT
    {"name": "Dima Hasao Watch", "corridor": "NH-27 Assam", "latitude": 25.2318, "longitude": 93.0146},
]

# Maps each corridor to the IMD meteorological subdivision that covers it.
# NOTE: double-check "Sub Himalayan West Bengal & Sikkim" against the actual
# SUBDIVISION values in the dataset's Preview tab before relying on it --
# IMD's exact spelling/casing can differ slightly from what's documented.
CORRIDOR_TO_SUBDIVISION = {
    "NH-10 Sikkim": "Sub Himalayan West Bengal & Sikkim",
    "Gangtok": "Sub Himalayan West Bengal & Sikkim",
    "NH-29 Nagaland": "Naga Mani Mizo Tripura",
    "NH-54 Mizoram": "Naga Mani Mizo Tripura",
    "NH-27 Assam": "Assam & Meghalaya",
}

MONTH_COLUMNS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# subdivision -> {month_number: avg_rainfall_mm}, filled once at startup
_REAL_RAINFALL_CACHE = {}


def _fetch_subdivision_monthly_avg(subdivision):
    """Pulls every year's row for one subdivision (1901-2017) and averages
    each month across all years -- a real historical baseline instead of
    an arbitrary number."""
    records = []
    offset = 0
    while True:
        params = {
            "api-key": DATAGOVIN_API_KEY,
            "format": "json",
            "limit": 100,
            "offset": offset,
            "filters[SUBDIVISION]": subdivision,
        }
        r = requests.get(
            f"https://api.data.gov.in/resource/{RAINFALL_RESOURCE_ID}",
            params=params, timeout=15,
        )
        r.raise_for_status()
        page = r.json().get("records", [])
        if not page:
            break
        records.extend(page)
        offset += len(page)

    monthly_values = {i: [] for i in range(1, 13)}
    for row in records:
        for i, month in enumerate(MONTH_COLUMNS, start=1):
            val = row.get(month)
            if val not in (None, "", "NA"):
                try:
                    monthly_values[i].append(float(val))
                except ValueError:
                    pass

    return {
        i: (sum(vals) / len(vals) if vals else 0.0)
        for i, vals in monthly_values.items()
    }


def _get_real_rainfall_baseline(corridor, month):
    subdivision = CORRIDOR_TO_SUBDIVISION.get(corridor)
    if not subdivision:
        return None
    if subdivision not in _REAL_RAINFALL_CACHE:
        print(f"Fetching real IMD rainfall history for '{subdivision}'...")
        _REAL_RAINFALL_CACHE[subdivision] = _fetch_subdivision_monthly_avg(subdivision)
    return _REAL_RAINFALL_CACHE[subdivision].get(month, 0.0)


def seed_sensors():
    existing = requests.get(f"{API_BASE}/sensors").json()
    if existing:
        print(f"{len(existing)} sensors already registered, reusing them.")
        return [(s["id"], s.get("corridor", "")) for s in existing]

    ids = []
    for s in SEED_SENSORS:
        r = requests.post(f"{API_BASE}/sensors", json=s)
        r.raise_for_status()
        sid = r.json()["id"]
        ids.append((sid, s["corridor"]))
        print(f"Registered sensor {s['name']} -> id {sid}")
    return ids


def random_reading(sensor_id, corridor, storm_mode=False):
    """storm_mode biases one sensor toward Warning/Danger so the demo has
    drama. Rainfall is grounded in the real IMD historical monthly average
    for this corridor's subdivision; everything else stays simulated since
    no public feed exists for displacement/pore pressure/slope angle."""
    baseline = _get_real_rainfall_baseline(corridor, datetime.utcnow().month) or 30.0

    if storm_mode:
        rainfall = baseline * random.uniform(1.8, 3.2)  # storm spike above real seasonal norm
        soil_moisture = random.uniform(70, 95)
        displacement = random.uniform(8, 18)
        pore_pressure = random.uniform(55, 90)
        slope_angle = random.uniform(35, 55)
    else:
        rainfall = baseline * random.uniform(0.4, 1.3)  # normal day, real seasonal norm +/- noise
        soil_moisture = random.uniform(20, 55)
        displacement = random.uniform(0, 3)
        pore_pressure = random.uniform(5, 35)
        slope_angle = random.uniform(15, 40)

    return {
        "sensor_id": sensor_id,
        "rainfall_mm": round(rainfall, 1),
        "soil_moisture_pct": round(soil_moisture, 1),
        "displacement_mm": round(displacement, 2),
        "pore_pressure_kpa": round(pore_pressure, 1),
        "slope_angle_deg": round(slope_angle, 1),
    }


def run(loop=True, interval=5, storm_sensor_index=0):
    ids = seed_sensors()
    while True:
        for i, (sid, corridor) in enumerate(ids):
            storm = (i == storm_sensor_index) and (random.random() < 0.4)
            payload = random_reading(sid, corridor, storm_mode=storm)
            r = requests.post(f"{API_BASE}/readings", json=payload)
            if r.ok:
                d = r.json()
                print(f"sensor {sid}: {d['risk_label']} (p={d['risk_probability']:.2f})")
            else:
                print(f"sensor {sid}: ingest failed -> {r.status_code} {r.text}")
        if not loop:
            break
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="single pass instead of looping")
    parser.add_argument("--interval", type=int, default=5, help="seconds between rounds")
    args = parser.parse_args()
    run(loop=not args.once, interval=args.interval)
