from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random
import math

app = FastAPI(title="MINESAFE Backend", version="1.0")

# Allow the Streamlit frontend to communicate with FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# DEMO VEHICLE DATA
# ---------------------------------------------------------
# This is a software-simulated backend for the MINESAFE
# dashboard. Later, the same API can be connected to ESP32,
# GNSS, radar, camera/CV and V2V telemetry.
# ---------------------------------------------------------

vehicles = [
    {
        "vehicle_id": "HEMM-01",
        "status": "Active",
        "risk": "LOW",
        "risk_score": 0.20,
        "speed": 5.0,
        "distance": 32.9,
        "ttc": 8.1,
        "visibility": 37.0,
        "temperature": 24.2,
        "humidity": 78.3,
        "latitude": 18.6365,
        "longitude": 81.2580,
        "target_speed": 20.0,
    },
    {
        "vehicle_id": "HEMM-02",
        "status": "Active",
        "risk": "LOW",
        "risk_score": 0.36,
        "speed": 13.0,
        "distance": 34.8,
        "ttc": 7.3,
        "visibility": 32.0,
        "temperature": 24.2,
        "humidity": 78.3,
        "latitude": 18.6383,
        "longitude": 81.2604,
        "target_speed": 20.0,
    },
    {
        "vehicle_id": "HEMM-03",
        "status": "Active",
        "risk": "MEDIUM",
        "risk_score": 0.55,
        "speed": 29.0,
        "distance": 14.4,
        "ttc": 9.0,
        "visibility": 85.0,
        "temperature": 24.2,
        "humidity": 78.3,
        "latitude": 18.6350,
        "longitude": 81.2612,
        "target_speed": 25.0,
    },
    {
        "vehicle_id": "HEMM-05",
        "status": "Active",
        "risk": "HIGH",
        "risk_score": 0.89,
        "speed": 5.0,
        "distance": 45.5,
        "ttc": 1.9,
        "visibility": 100.0,
        "temperature": 24.2,
        "humidity": 78.3,
        "latitude": 18.6393,
        "longitude": 81.2562,
        "target_speed": 5.0,
    },
    {
        "vehicle_id": "HEMM-07",
        "status": "Active",
        "risk": "HIGH",
        "risk_score": 0.78,
        "speed": 19.0,
        "distance": 26.8,
        "ttc": 1.5,
        "visibility": 86.0,
        "temperature": 24.2,
        "humidity": 78.3,
        "latitude": 18.6341,
        "longitude": 81.2550,
        "target_speed": 10.0,
    },
    {
        "vehicle_id": "HEMM-11",
        "status": "Active",
        "risk": "HIGH",
        "risk_score": 0.81,
        "speed": 15.0,
        "distance": 9.9,
        "ttc": 3.4,
        "visibility": 99.0,
        "temperature": 24.2,
        "humidity": 78.3,
        "latitude": 18.6400,
        "longitude": 81.2618,
        "target_speed": 10.0,
    },
]


def update_demo_values():
    """Small realistic changes so the dashboard feels live."""
    for v in vehicles:
        # Keep values inside sensible demo ranges.
        v["speed"] = round(max(0, v["speed"] + random.uniform(-1.0, 1.0)), 1)
        v["distance"] = round(
            max(5.0, v["distance"] + random.uniform(-1.5, 1.5)), 1
        )
        v["ttc"] = round(max(1.0, v["ttc"] + random.uniform(-0.25, 0.25)), 1)

        # Visibility changes slowly, because it is an environmental
        # parameter rather than a rapidly fluctuating vehicle parameter.
        v["visibility"] = round(
            max(10.0, v["visibility"] + random.uniform(-0.8, 0.8)), 1
        )

        # Risk score follows the current safety indicators.
        distance_factor = max(0.0, min(1.0, (50.0 - v["distance"]) / 50.0))
        ttc_factor = max(0.0, min(1.0, (8.0 - v["ttc"]) / 8.0))
        speed_factor = max(0.0, min(1.0, v["speed"] / 35.0))

        score = (
            0.45 * distance_factor
            + 0.40 * ttc_factor
            + 0.15 * speed_factor
        )

        # Blend slightly with the original demo score so the
        # risk category does not jump around unnecessarily.
        v["risk_score"] = round(
            max(0.0, min(1.0, 0.75 * v["risk_score"] + 0.25 * score)),
            2,
        )

        if v["risk_score"] >= 0.70:
            v["risk"] = "HIGH"
        elif v["risk_score"] >= 0.45:
            v["risk"] = "MEDIUM"
        else:
            v["risk"] = "LOW"


# ---------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "system": "MINESAFE",
        "status": "online",
        "message": "MINESAFE FastAPI backend is running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "v2v_network": "Connected",
        "rsu_network": "Online",
        "gnss_status": "Good",
    }


@app.get("/fleet")
def get_fleet():
    update_demo_values()

    return {
        "system": "MINESAFE",
        "timestamp": datetime.now().isoformat(),
        "vehicles": vehicles,
    }


@app.get("/vehicle/{vehicle_id}")
def get_vehicle(vehicle_id: str):
    update_demo_values()

    for vehicle in vehicles:
        if vehicle["vehicle_id"].lower() == vehicle_id.lower():
            return vehicle

    return {
        "error": "Vehicle not found",
        "vehicle_id": vehicle_id,
    }


@app.get("/alerts")
def get_alerts():
    update_demo_values()

    alerts = []

    for v in vehicles:
        if v["risk"] == "HIGH":
            alerts.append({
                "vehicle_id": v["vehicle_id"],
                "level": "HIGH",
                "distance": v["distance"],
                "ttc": v["ttc"],
                "risk_score": v["risk_score"],
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })
        elif v["risk"] == "MEDIUM":
            alerts.append({
                "vehicle_id": v["vehicle_id"],
                "level": "MEDIUM",
                "distance": v["distance"],
                "ttc": v["ttc"],
                "risk_score": v["risk_score"],
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })

    return {
        "count": len(alerts),
        "alerts": alerts,
    }


@app.get("/system/status")
def system_status():
    return {
        "cameras": "24/24 Online",
        "radars": "18/18 Online",
        "rsus": "6/6 Online",
        "edge_servers": "2/2 Online",
        "v2v_network": "Connected",
        "database": "Healthy",
    }


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------
# Start with:
#     uvicorn backend:app --reload --port 8000
#
# Or:
#     python backend.py
# ---------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
