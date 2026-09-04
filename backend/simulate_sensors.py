"""
Stand-in for real IoT hardware. Run this alongside the API server so the
map/alerts/officer console have live data to react to during your demo.

Usage:
  python simulate_sensors.py            # seeds 5 NER-corridor sensors, then loops forever
  python simulate_sensors.py --once     # single pass (useful for testing)

Env:
  API_BASE (default http://localhost:8000)
"""
import argparse
import os
import random
import time
import requests

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# Rough points along real NER landslide-prone corridors mentioned in the PPT
SEED_SENSORS = [
    {"name": "NH-10 KM 42", "corridor": "NH-10 Sikkim", "latitude": 27.0410, "longitude": 88.2661},
    {"name": "NH-10 KM 58", "corridor": "NH-10 Sikkim", "latitude": 27.0710, "longitude": 88.2890},
    {"name": "Gangtok Bypass", "corridor": "Gangtok", "latitude": 27.3389, "longitude": 88.6065},
    {"name": "Kohima Slope Watch", "corridor": "NH-29 Nagaland", "latitude": 25.6751, "longitude": 94.1086},
    {"name": "Aizawl Ridge", "corridor": "NH-54 Mizoram", "latitude": 23.7271, "longitude": 92.7176},
]


def seed_sensors():
    ids = []
    existing = requests.get(f"{API_BASE}/sensors").json()
    if existing:
        print(f"{len(existing)} sensors already registered, reusing them.")
        return [s["id"] for s in existing]
    for s in SEED_SENSORS:
        r = requests.post(f"{API_BASE}/sensors", json=s)
        r.raise_for_status()
        ids.append(r.json()["id"])
        print(f"Registered sensor {s['name']} -> id {r.json()['id']}")
    return ids


def random_reading(sensor_id, storm_mode=False):
    """storm_mode biases one sensor toward Warning/Danger so the demo has drama."""
    if storm_mode:
        rainfall = random.uniform(120, 240)
        soil_moisture = random.uniform(70, 95)
        displacement = random.uniform(8, 18)
        pore_pressure = random.uniform(55, 90)
        slope_angle = random.uniform(35, 55)
    else:
        rainfall = random.uniform(0, 60)
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
        for i, sid in enumerate(ids):
            storm = (i == storm_sensor_index) and (random.random() < 0.4)
            payload = random_reading(sid, storm_mode=storm)
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
