import streamlit as st
import requests
import pandas as pd
import numpy as np
import pydeck as pdk
import time
from datetime import datetime


# =========================================================
# CONFIG
# =========================================================

BACKEND_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="MINESAFE Control Room",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background: #061018;
}

.block-container {
    padding-top: 0.4rem !important;
    padding-bottom: 2rem;
    max-width: 1550px;
}

header[data-testid="stHeader"] {
    background: transparent;
    height: 2.2rem;
}

section[data-testid="stSidebar"] {
    background: #08131c;
    border-right: 1px solid #1c303d;
}

h1, h2, h3 {
    letter-spacing: 0.2px;
}

div[data-testid="stMetric"] {
    background: #0b1923;
    border: 1px solid #203442;
    border-radius: 8px;
    padding: 10px;
}

div[data-testid="stMetricValue"] {
    font-size: 24px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #0a1721;
    border-color: #203442;
}

.alert-high {
    background: #291115;
    border: 1px solid #69252b;
    border-radius: 8px;
    padding: 10px;
}

.alert-medium {
    background: #28200d;
    border: 1px solid #665018;
    border-radius: 8px;
    padding: 10px;
}

.alert-info {
    background: #0d1d2c;
    border: 1px solid #254b6a;
    border-radius: 8px;
    padding: 10px;
}

.small {
    font-size: 12px;
    color: #8fa1af;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

if "selected_vehicle" not in st.session_state:
    st.session_state.selected_vehicle = "HEMM-02"

if "history" not in st.session_state:
    st.session_state.history = []

if "events" not in st.session_state:
    st.session_state.events = []

if "emergency_stop" not in st.session_state:
    st.session_state.emergency_stop = False

if "operator_open" not in st.session_state:
    st.session_state.operator_open = False


# =========================================================
# BACKEND
# =========================================================

def get_fleet():

    try:

        response = requests.get(
            f"{BACKEND_URL}/fleet",
            timeout=3
        )

        if response.status_code == 200:
            return response.json()

        return None

    except requests.exceptions.RequestException:
        return None


fleet_response = get_fleet()


if not fleet_response:

    st.error(
        "Backend disconnected. "
        "Please start FastAPI first."
    )

    st.stop()


vehicles = fleet_response["vehicles"]


# =========================================================
# CALCULATIONS
# =========================================================

total = len(vehicles)

active = sum(
    v["status"] == "Active"
    for v in vehicles
)

high = sum(
    v["risk"] == "HIGH"
    for v in vehicles
)

medium = sum(
    v["risk"] == "MEDIUM"
    for v in vehicles
)

low = sum(
    v["risk"] == "LOW"
    for v in vehicles
)

avg_speed = round(
    sum(v["speed"] for v in vehicles) / total,
    1
)

avg_ttc = round(
    sum(v["ttc"] for v in vehicles) / total,
    1
)

avg_visibility = round(
    sum(v["visibility"] for v in vehicles) / total,
    1
)

avg_temperature = round(
    sum(v["temperature"] for v in vehicles) / total,
    1
)

avg_humidity = round(
    sum(v["humidity"] for v in vehicles) / total,
    1
)

active_alerts = high + medium


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## ⛏️ MINESAFE")
    st.caption("Control Room")

    st.divider()

    st.markdown("### Navigation")

    page = st.radio(
        "Select View",
        [
            "Overview",
            "Live Monitoring",
            "Fleet Map",
            "Alerts & Events",
            "Vehicle Dashboard",
            "Analytics"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("### Operator")

    if st.button("Operator-01", key="operator_01_btn", use_container_width=True):
        st.session_state.operator_open = not st.session_state.get("operator_open", False)
        st.session_state.events.append(
            f"{datetime.now().strftime('%H:%M:%S')} — Operator-01 profile opened"
        )

    if st.session_state.get("operator_open", False):
        st.info("Operator-01\nControl Room\nRole: Safety Monitoring")

    st.success("System Online")


# =========================================================
# HEADER
# =========================================================

top1, top2, top3, top4, top5, top6 = st.columns(
    [2.0, 1, 1, 1, 1, 1]
)

with top1:

    st.title("⛏️ MINESAFE")
    st.caption(
        "Control Room • Real-Time Mine Vehicle Safety"
    )

with top2:
    st.metric(
        "TOTAL HEMMs",
        total,
        f"{active} Active"
    )

with top3:
    st.metric(
        "HIGH RISK",
        high
    )

with top4:
    st.metric(
        "MEDIUM RISK",
        medium
    )

with top5:
    st.metric(
        "LOW RISK",
        low
    )

with top6:
    st.metric(
        "ACTIVE ALERTS",
        active_alerts
    )


st.divider()


# =========================================================
# NETWORK STATUS
# =========================================================

n1, n2, n3, n4 = st.columns(4)

with n1:
    st.success("V2V Network — Connected")

with n2:
    st.success("RSU Network — Online")

with n3:
    st.success("GNSS Status — Good")

with n4:
    st.info(
        f"{datetime.now().strftime('%H:%M:%S')}"
    )


# =========================================================
# OVERVIEW
# =========================================================

# =========================================================
# KIRANDUL / BAILADILA MAP DISPLAY ONLY
# =========================================================
# Only the map display is relocated to the project site.
# Backend vehicle telemetry and all other dashboard values remain unchanged.
KIRANDUL_LAT = 18.6365
KIRANDUL_LON = 81.2580

KIRANDUL_OFFSETS = [
    (0.0000, 0.0000),
    (0.0018, 0.0024),
    (-0.0015, 0.0032),
    (0.0028, -0.0018),
    (-0.0024, -0.0030),
    (0.0035, 0.0038),
]

if page == "Overview":

    st.subheader("Control Room Overview")

    # -----------------------------------------------------
    # ROW 1
    # -----------------------------------------------------

    col1, col2, col3 = st.columns([1.1, 1.2, 1.2])

    # FLEET OVERVIEW
    with col1:

        with st.container(border=True):

            st.markdown("### Fleet Overview")

            fleet_chart = pd.DataFrame({
                "Risk": [
                    "High Risk",
                    "Medium Risk",
                    "Low Risk"
                ],
                "Vehicles": [
                    high,
                    medium,
                    low
                ]
            })

            st.vega_lite_chart(
                fleet_chart,
                {
                    "mark": {
                        "type": "arc",
                        "innerRadius": 55
                    },
                    "encoding": {
                        "theta": {
                            "field": "Vehicles",
                            "type": "quantitative"
                        },
                        "color": {
                            "field": "Risk",
                            "type": "nominal",
                            "scale": {
                                "domain": [
                                    "High Risk",
                                    "Medium Risk",
                                    "Low Risk"
                                ],
                                "range": [
                                    "#ef4444",
                                    "#f59e0b",
                                    "#22c55e"
                                ]
                            },
                            "legend": {
                                "orient": "bottom"
                            }
                        }
                    },
                    "width": "container",
                    "height": 190
                }
            )

    # VISIBILITY
    with col2:

        with st.container(border=True):

            st.markdown(
                "### Visibility & Environment"
            )

            if avg_visibility < 20:
                st.error("🌫️ DENSE FOG")
            elif avg_visibility < 50:
                st.warning("🌫️ LOW VISIBILITY")
            else:
                st.success("☀️ GOOD VISIBILITY")

            st.metric(
                "Visibility",
                f"{avg_visibility} m"
            )

            e1, e2 = st.columns(2)

            with e1:
                st.write(
                    f"Temperature: **{avg_temperature} °C**"
                )

                st.write(
                    f"Humidity: **{avg_humidity}%**"
                )

            with e2:
                st.write(
                    f"Avg Speed: **{avg_speed} km/h**"
                )

                st.write(
                    f"Avg TTC: **{avg_ttc} sec**"
                )

    # ALERT SUMMARY
    with col3:

        with st.container(border=True):

            st.markdown(
                "### Alert Summary — Today"
            )

            a1, a2, a3 = st.columns(3)

            with a1:
                st.metric(
                    "Critical",
                    high
                )

            with a2:
                st.metric(
                    "Warning",
                    medium
                )

            with a3:
                st.metric(
                    "Info",
                    max(0, total - high - medium)
                )

            st.divider()

            if high > 0:

                highest = next(
                    v for v in vehicles
                    if v["risk"] == "HIGH"
                )

                st.write(
                    f"Last Alert: **{highest['vehicle_id']} "
                    f"High Risk**"
                )

            else:

                st.write(
                    "Last Alert: No critical event"
                )


    # -----------------------------------------------------
    # SYSTEM HEALTH
    # -----------------------------------------------------

    st.subheader("🖥️ System Health")

    h1, h2, h3, h4, h5, h6 = st.columns(6)

    with h1:
        st.success("Cameras\n24/24 Online")

    with h2:
        st.success("Radars\n18/18 Online")

    with h3:
        st.success("RSUs\n6/6 Online")

    with h4:
        st.success("Edge Servers\n2/2 Online")

    with h5:
        st.success("V2V Network\nConnected")

    with h6:
        st.success("Database\nHealthy")


    # =====================================================
    # MINE MAP
    # =====================================================

    st.subheader("🗺️ MINE MAP — LIVE TRACKING")

    # Create mine-style abstract coordinates
    road1_x = np.linspace(0, 100, 100)
    road1_y = 50 + 10 * np.sin(
        road1_x / 12
    )

    road2_x = np.linspace(10, 90, 100)
    road2_y = 20 + 8 * np.sin(
        road2_x / 10
    )

    road3_x = np.linspace(15, 85, 100)
    road3_y = 80 + 7 * np.cos(
        road3_x / 11
    )

    roads = pd.DataFrame({

        "x": np.concatenate([
            road1_x,
            road2_x,
            road3_x
        ]),

        "y": np.concatenate([
            road1_y,
            road2_y,
            road3_y
        ]),

        "road": (
            ["Haul Road 1"] * 100 +
            ["Haul Road 2"] * 100 +
            ["Haul Road 3"] * 100
        )
    })

    # Vehicle positions
    vehicle_map = []

    for i, v in enumerate(vehicles):

        x = 15 + (
            i * 13
        )

        y = 25 + (
            (i % 3) * 25
        )

        vehicle_map.append({

            "x": x,
            "y": y,
            "vehicle": v["vehicle_id"],
            "risk": v["risk"]

        })

    vehicle_map = pd.DataFrame(
        vehicle_map
    )

    # RSU positions
    rsu_map = pd.DataFrame({

        "x": [18, 48, 78, 85],

        "y": [70, 35, 72, 20],

        "rsu": [
            "RSU-01",
            "RSU-03",
            "RSU-05",
            "RSU-06"
        ],

        "status": [
            "Online",
            "Online",
            "Online",
            "Online"
        ]

    })

    # Mine tracking chart
    st.vega_lite_chart(

        {
            "roads": roads.to_dict(
                orient="records"
            ),

            "vehicles": vehicle_map.to_dict(
                orient="records"
            ),

            "rsus": rsu_map.to_dict(
                orient="records"
            )
        },

        {
            "params": [
                {
                    "name": "map_navigation",
                    "select": {"type": "interval", "bind": "scales"}
                }
            ],
            "layer": [

                {
                    "data": {
                        "name": "roads"
                    },

                    "mark": {
                        "type": "line",
                        "strokeWidth": 3
                    },

                    "encoding": {
                        "x": {
                            "field": "x",
                            "type": "quantitative",
                            "axis": None
                        },

                        "y": {
                            "field": "y",
                            "type": "quantitative",
                            "axis": None
                        },

                        "detail": {
                            "field": "road"
                        }
                    }
                },

                {
                    "data": {
                        "name": "vehicles"
                    },

                    "mark": {
                        "type": "point",
                        "filled": True,
                        "size": 350
                    },

                    "encoding": {
                        "x": {
                            "field": "x",
                            "type": "quantitative"
                        },

                        "y": {
                            "field": "y",
                            "type": "quantitative"
                        },

                        "color": {
                            "field": "risk",
                            "type": "nominal",
                            "scale": {
                                "domain": [
                                    "HIGH",
                                    "MEDIUM",
                                    "LOW"
                                ],
                                "range": [
                                    "#ef4444",
                                    "#f59e0b",
                                    "#22c55e"
                                ]
                            }
                        },

                        "tooltip": [
                            {
                                "field": "vehicle"
                            },
                            {
                                "field": "risk"
                            }
                        ]
                    }
                },

                {
                    "data": {
                        "name": "rsus"
                    },

                    "mark": {
                        "type": "point",
                        "shape": "triangle-up",
                        "size": 250,
                        "color": "#4da3ff"
                    },

                    "encoding": {
                        "x": {
                            "field": "x",
                            "type": "quantitative"
                        },

                        "y": {
                            "field": "y",
                            "type": "quantitative"
                        },

                        "tooltip": [
                            {
                                "field": "rsu"
                            },
                            {
                                "field": "status"
                            }
                        ]
                    }
                },

                {
                    "data": {
                        "name": "rsus"
                    },
                    "mark": {
                        "type": "text",
                        "dy": -18,
                        "fontSize": 12,
                        "fontWeight": "bold"
                    },
                    "encoding": {
                        "x": {"field": "x", "type": "quantitative"},
                        "y": {"field": "y", "type": "quantitative"},
                        "text": {"field": "rsu", "type": "nominal"},
                        "color": {"value": "#8ecbff"}
                    }
                }

            ],

            "width": "container",

            "height": 420,

            "config": {
                "background": "#08131c",
                "view": {
                    "stroke": "#263a48"
                },

                "axis": {
                    "grid": True,
                    "gridColor": "#20303b",
                    "labelColor": "#8295a3",
                    "titleColor": "#8295a3"
                }
            }
        }
    )


    # =====================================================
    # FLEET STATISTICS
    # =====================================================

    st.subheader("📊 Fleet Statistics")

    s1, s2, s3, s4, s5 = st.columns(5)

    total_distance = round(
        sum(v["distance"] for v in vehicles),
        1
    )

    near_miss = high

    with s1:
        st.metric(
            "Average Speed",
            f"{avg_speed} km/h"
        )

    with s2:
        st.metric(
            "Average TTC",
            f"{avg_ttc} sec"
        )

    with s3:
        st.metric(
            "Total Distance",
            f"{total_distance} km"
        )

    with s4:
        st.metric(
            "Safe Zone Violations",
            max(1, medium)
        )

    with s5:
        st.metric(
            "Near Miss Events",
            near_miss
        )


    # =====================================================
    # ACTIVE ALERTS
    # =====================================================

    st.subheader("⚠️ Active Alerts")

    if active_alerts == 0:

        st.success(
            "🟢 No active alerts"
        )

    else:

        for v in vehicles:

            if v["risk"] == "HIGH":

                st.error(
                    f"🔴 HIGH RISK — {v['vehicle_id']} | "
                    f"Distance: {v['distance']} m | "
                    f"TTC: {v['ttc']} s"
                )

            elif v["risk"] == "MEDIUM":

                st.warning(
                    f"🟡 MEDIUM RISK — {v['vehicle_id']} | "
                    f"Distance: {v['distance']} m"
                )


    # =====================================================
    # QUICK ACTIONS
    # =====================================================

    st.subheader("⚡ Quick Actions")

    q1, q2, q3, q4 = st.columns(4)

    with q1:

        if st.button(
            "Emergency Stop",
            use_container_width=True
        ):

            st.session_state.emergency_stop = True

            st.session_state.events.append(
                f"{datetime.now().strftime('%H:%M:%S')} — "
                "Emergency Stop activated"
            )

            st.error(
                "🛑 Emergency Stop Active"
            )


    with q2:

        if st.button(
            "Acknowledge Alerts",
            use_container_width=True
        ):

            st.session_state.events.append(
                f"{datetime.now().strftime('%H:%M:%S')} — "
                "Alerts acknowledged"
            )

            st.success(
                "Alerts acknowledged."
            )


    with q3:

        if st.button(
            "System Diagnostics",
            use_container_width=True
        ):

            st.info(
                "All software monitoring services "
                "are responding."
            )


    with q4:

        if st.button(
            "Generate Report",
            use_container_width=True
        ):

            st.info(
                "Report generation module ready "
                "for final integration."
            )


# =========================================================
# LIVE MONITORING
# =========================================================

elif page == "Live Monitoring":

    st.subheader("📡 Live Monitoring")

    selected = st.selectbox(
        "Select HEMM",
        [
            v["vehicle_id"]
            for v in vehicles
        ]
    )

    vehicle = next(
        v for v in vehicles
        if v["vehicle_id"] == selected
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "Speed",
            f'{vehicle["speed"]} km/h'
        )

    with c2:
        st.metric(
            "Distance",
            f'{vehicle["distance"]} m'
        )

    with c3:
        st.metric(
            "TTC",
            f'{vehicle["ttc"]} sec'
        )

    with c4:
        st.metric(
            "Visibility",
            f'{vehicle["visibility"]} m'
        )

    with c5:
        st.metric(
            "Risk",
            vehicle["risk"]
        )

    st.divider()

    if vehicle["risk"] == "HIGH":
        st.error(
            "🔴 HIGH COLLISION RISK"
        )

    elif vehicle["risk"] == "MEDIUM":
        st.warning(
            "🟡 MEDIUM RISK"
        )

    else:
        st.success(
            "🟢 LOW RISK"
        )


# =========================================================
# FLEET MAP
# =========================================================

elif page == "Fleet Map":

    st.subheader("Fleet Map")

    # Bailadila Mining Complex / Kirandul, Chhattisgarh
    map_points = []
    for i, v in enumerate(vehicles):
        dlat, dlon = KIRANDUL_OFFSETS[i % len(KIRANDUL_OFFSETS)]
        map_points.append({
            "vehicle_id": v["vehicle_id"],
            "latitude": KIRANDUL_LAT + dlat,
            "longitude": KIRANDUL_LON + dlon,
            "risk": v["risk"],
            "speed": v["speed"],
        })

    map_df = pd.DataFrame(map_points)

    # Static RSU locations with visible names and online status.
    rsu_points = pd.DataFrame({
        "rsu": ["RSU-01", "RSU-03", "RSU-05", "RSU-06"],
        "status": ["Online", "Online", "Online", "Online"],
        "latitude": [
            KIRANDUL_LAT + 0.0012,
            KIRANDUL_LAT - 0.0010,
            KIRANDUL_LAT + 0.0027,
            KIRANDUL_LAT - 0.0020,
        ],
        "longitude": [
            KIRANDUL_LON - 0.0022,
            KIRANDUL_LON + 0.0028,
            KIRANDUL_LON + 0.0015,
            KIRANDUL_LON - 0.0030,
        ],
    })

    vehicle_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[longitude, latitude]",
        get_radius=32,
        get_fill_color="risk == 'HIGH' ? [239,68,68] : risk == 'MEDIUM' ? [245,158,11] : [34,197,94]",
        pickable=True,
        stroked=True,
        get_line_color=[255, 255, 255],
        get_line_width=2,
    )

    vehicle_labels = pdk.Layer(
        "TextLayer",
        data=map_df,
        get_position="[longitude, latitude]",
        get_text="vehicle_id",
        get_size=13,
        get_color=[255, 255, 255],
        get_pixel_offset=[0, -28],
        billboard=True,
        pickable=False,
    )

    rsu_layer = pdk.Layer(
        "ScatterplotLayer",
        data=rsu_points,
        get_position="[longitude, latitude]",
        get_radius=24,
        get_fill_color=[77, 163, 255],
        get_line_color=[255, 255, 255],
        get_line_width=2,
        stroked=True,
        pickable=True,
    )

    rsu_labels = pdk.Layer(
        "TextLayer",
        data=rsu_points,
        get_position="[longitude, latitude]",
        get_text="rsu + ' (Online)'",
        get_size=12,
        get_color=[142, 203, 255],
        get_pixel_offset=[0, -25],
        billboard=True,
        pickable=False,
    )

    view_state = pdk.ViewState(
        latitude=KIRANDUL_LAT,
        longitude=KIRANDUL_LON,
        zoom=13.8,
        pitch=0,
        bearing=0,
    )

    deck = pdk.Deck(
        layers=[vehicle_layer, vehicle_labels, rsu_layer, rsu_labels],
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={
            "html": "<b>{vehicle_id}</b><br/>Risk: {risk}<br/>Speed: {speed} km/h",
            "style": {"backgroundColor": "#101820", "color": "white"},
        },
    )

    st.pydeck_chart(deck, use_container_width=True, height=520)
    st.caption("Bailadila Mining Complex • Kirandul, Chhattisgarh")

    st.dataframe(
        pd.DataFrame(vehicles)[
            [
                "vehicle_id",
                "latitude",
                "longitude",
                "risk",
                "speed"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# ALERTS
# =========================================================

elif page == "Alerts & Events":

    st.subheader("⚠️ Alerts & Events")

    for v in vehicles:

        if v["risk"] == "HIGH":

            st.error(
                f"🔴 HIGH — {v['vehicle_id']} | "
                f"TTC {v['ttc']} sec | "
                f"Distance {v['distance']} m"
            )

        elif v["risk"] == "MEDIUM":

            st.warning(
                f"🟡 MEDIUM — {v['vehicle_id']} | "
                f"Distance {v['distance']} m"
            )

    st.divider()

    st.subheader("📋 Event Log")

    if st.session_state.events:

        for event in reversed(
            st.session_state.events[-20:]
        ):

            st.write(
                f"• {event}"
            )

    else:

        st.info(
            "No operator events yet."
        )


# =========================================================
# INDIVIDUAL VEHICLE DASHBOARD
# =========================================================

elif page == "Vehicle Dashboard":

    st.subheader(
        "🚛 Individual HEMM Dashboard"
    )

    vehicle_names = [
        v["vehicle_id"]
        for v in vehicles
    ]

    selected = st.selectbox(
        "Select Vehicle",
        vehicle_names,
        index=(
            vehicle_names.index(
                st.session_state.selected_vehicle
            )
            if st.session_state.selected_vehicle
            in vehicle_names
            else 0
        )
    )

    st.session_state.selected_vehicle = selected

    vehicle = next(
        v for v in vehicles
        if v["vehicle_id"] == selected
    )


    # -----------------------------------------------------
    # VEHICLE HEADER
    # -----------------------------------------------------

    st.markdown(
        f"## 🚛 {vehicle['vehicle_id']} — Dump Truck"
    )

    st.caption(
        "Vehicle Dashboard • Live Sensor Monitoring"
    )


    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.metric(
            "SPEED",
            f'{vehicle["speed"]} km/h'
        )

    with c2:
        st.metric(
            "DISTANCE",
            f'{vehicle["distance"]} m'
        )

    with c3:
        st.metric(
            "TTC",
            f'{vehicle["ttc"]} sec'
        )

    with c4:
        st.metric(
            "RISK SCORE",
            f'{vehicle["risk_score"]:.2f} / 1.00'
        )

    with c5:
        st.metric(
            "TARGET SPEED",
            f'{vehicle["recommended_speed"]} km/h'
        )

    with c6:
        st.metric(
            "STATUS",
            vehicle["status"]
        )


    # -----------------------------------------------------
    # THREE MAIN PANELS
    # -----------------------------------------------------

    p1, p2, p3 = st.columns(
        [1.1, 1.1, 1]
    )


    # CAMERA PANEL
    with p1:

        with st.container(border=True):

            st.markdown(
                "### Live Camera View"
            )

            camera = pd.DataFrame({

                "x": [0, 100],
                "y": [0, 100]

            })

            st.vega_lite_chart(
                camera,
                {
                    "mark": {
                        "type": "rect",
                        "fill": "#182a36"
                    },
                    "encoding": {
                        "x": {
                            "field": "x",
                            "type": "quantitative"
                        },
                        "y": {
                            "field": "y",
                            "type": "quantitative"
                        }
                    },
                    "width": "container",
                    "height": 250,
                    "config": {
                        "axis": None,
                        "view": {
                            "stroke": "#304652"
                        }
                    }
                }
            )

            if vehicle["risk"] == "HIGH":

                st.error(
                    f"🚨 DETECTED — {vehicle['vehicle_id']}"
                )

            else:

                st.success(
                    "📷 Camera stream simulation active"
                )


    # OBJECTS
    with p2:

        with st.container(border=True):

            st.markdown(
                "### Detected Objects"
            )

            if vehicle["risk"] == "HIGH":

                st.error(
                    f"🚛 Nearby HEMM\n\n"
                    f"Distance: {vehicle['distance']} m\n\n"
                    f"TTC: {vehicle['ttc']} sec\n\n"
                    f"Risk: HIGH"
                )

                st.warning(
                    "👷 Worker detected nearby"
                )

            elif vehicle["risk"] == "MEDIUM":

                st.warning(
                    "🚛 Vehicle detected\n\n"
                    f"Distance: {vehicle['distance']} m"
                )

            else:

                st.success(
                    "🟢 No critical object detected"
                )


    # SAFETY
    with p3:

        with st.container(border=True):

            st.markdown(
                "### Safety Status"
            )

            if vehicle["risk"] == "HIGH":

                st.error("🔴 HIGH RISK")

            elif vehicle["risk"] == "MEDIUM":

                st.warning("🟡 MEDIUM RISK")

            else:

                st.success("🟢 LOW RISK")

            st.write(
                f"Risk Score: **{vehicle['risk_score']:.2f}**"
            )

            st.write(
                f"TTC: **{vehicle['ttc']} sec**"
            )

            st.write(
                f"Distance: **{vehicle['distance']} m**"
            )


    # -----------------------------------------------------
    # TRAJECTORY
    # -----------------------------------------------------

    st.subheader(
        "🎯 Trajectory & Safety Zone"
    )

    trajectory = pd.DataFrame({

        "x": np.linspace(0, 100, 50),

        "y": (
            50 +
            18 * np.sin(
                np.linspace(0, 3, 50)
            )
        )

    })

    st.vega_lite_chart(

        trajectory,

        {

            "layer": [

                {
                    "data": {
                        "values": [
                            {
                                "x": 50,
                                "y": 50,
                                "radius": 35
                            }
                        ]
                    },

                    "mark": {
                        "type": "circle",
                        "opacity": 0.18
                    },

                    "encoding": {
                        "x": {
                            "field": "x",
                            "type": "quantitative"
                        },

                        "y": {
                            "field": "y",
                            "type": "quantitative"
                        },

                        "size": {
                            "field": "radius",
                            "type": "quantitative"
                        },

                        "color": {
                            "value": "#22c55e"
                        }
                    }
                },

                {
                    "data": {
                        "values": [
                            {
                                "x": 50,
                                "y": 50,
                                "radius": 18
                            }
                        ]
                    },

                    "mark": {
                        "type": "circle",
                        "opacity": 0.18
                    },

                    "encoding": {
                        "x": {
                            "field": "x",
                            "type": "quantitative"
                        },

                        "y": {
                            "field": "y",
                            "type": "quantitative"
                        },

                        "size": {
                            "field": "radius",
                            "type": "quantitative"
                        },

                        "color": {
                            "value": "#f59e0b"
                        }
                    }
                },

                {
                    "data": {
                        "values": [
                            {
                                "x": 50,
                                "y": 50,
                                "radius": 8
                            }
                        ]
                    },

                    "mark": {
                        "type": "circle",
                        "opacity": 0.25
                    },

                    "encoding": {
                        "x": {
                            "field": "x",
                            "type": "quantitative"
                        },

                        "y": {
                            "field": "y",
                            "type": "quantitative"
                        },

                        "size": {
                            "field": "radius",
                            "type": "quantitative"
                        },

                        "color": {
                            "value": "#ef4444"
                        }
                    }
                },

                {
                    "data": {
                        "values":
                        trajectory.to_dict(
                            orient="records"
                        )
                    },

                    "mark": {
                        "type": "line",
                        "strokeDash": [6, 4],
                        "strokeWidth": 3
                    },

                    "encoding": {
                        "x": {
                            "field": "x",
                            "type": "quantitative"
                        },

                        "y": {
                            "field": "y",
                            "type": "quantitative"
                        }
                    }
                }

            ],

            "width": "container",

            "height": 330,

            "config": {
                "background": "#08131c",
                "axis": {
                    "gridColor": "#20303b",
                    "labelColor": "#8295a3"
                }
            }
        }
    )


    # -----------------------------------------------------
    # VEHICLE STATUS
    # -----------------------------------------------------

    st.subheader(
        "📡 Vehicle System Status"
    )

    s1, s2, s3, s4, s5, s6 = st.columns(6)

    with s1:
        st.success("🟢 Speed")

    with s2:
        st.success("🟢 GNSS")

    with s3:
        st.success("🟢 Radar")

    with s4:
        st.success("🟢 V2V")

    with s5:
        st.success("🟢 Battery")

    with s6:
        st.success("🟢 Health")


    # -----------------------------------------------------
    # RECOMMENDED ACTION
    # -----------------------------------------------------

    st.subheader(
        "🎯 Recommended Action"
    )

    if vehicle["risk"] == "HIGH":

        st.error(
            f"🔴 REDUCE SPEED — Target "
            f"{vehicle['recommended_speed']} km/h"
        )

    elif vehicle["risk"] == "MEDIUM":

        st.warning(
            f"🟡 REDUCE SPEED — Target "
            f"{vehicle['recommended_speed']} km/h"
        )

    else:

        st.success(
            "🟢 CONTINUE — Current conditions acceptable"
        )


    # -----------------------------------------------------
    # LOCATION
    # -----------------------------------------------------

    st.subheader(
        "📍 Vehicle GNSS Location"
    )

    loc1, loc2, loc3 = st.columns(3)

    with loc1:
        st.metric(
            "Latitude",
            f'{vehicle["latitude"]:.6f}'
        )

    with loc2:
        st.metric(
            "Longitude",
            f'{vehicle["longitude"]:.6f}'
        )

    with loc3:
        st.metric(
            "GNSS",
            "Locked"
        )


    # -----------------------------------------------------
    # MAP
    # -----------------------------------------------------

    # Display-only location: keep telemetry values above unchanged.
    selected_index = next(
        (i for i, v in enumerate(vehicles)
         if v["vehicle_id"] == vehicle["vehicle_id"]),
        0
    )
    dlat, dlon = KIRANDUL_OFFSETS[selected_index % len(KIRANDUL_OFFSETS)]

    location_df = pd.DataFrame({
        "latitude": [KIRANDUL_LAT + dlat],
        "longitude": [KIRANDUL_LON + dlon]
    })

    st.map(
        location_df,
        latitude="latitude",
        longitude="longitude",
        zoom=15,
        size=60
    )
    st.caption("Bailadila Mining Complex • Kirandul, Chhattisgarh")


    # Live graphs intentionally omitted from the vehicle display: space is limited.


# =========================================================
# ANALYTICS
# =========================================================

elif page == "Analytics":

    st.subheader(
        "📈 Analytics & Reports"
    )

    analytics_df = pd.DataFrame({

        "Vehicle": [
            v["vehicle_id"]
            for v in vehicles
        ],

        "Speed (km/h)": [
            v["speed"]
            for v in vehicles
        ],

        "Distance (m)": [
            v["distance"]
            for v in vehicles
        ],

        "TTC (sec)": [
            v["ttc"]
            for v in vehicles
        ],

        "Visibility (m)": [
            v["visibility"]
            for v in vehicles
        ],

        "Risk Score": [
            v["risk_score"]
            for v in vehicles
        ]

    })

    st.dataframe(
        analytics_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Speed Comparison (km/h)")

    st.bar_chart(
        analytics_df.set_index(
            "Vehicle"
        )[["Speed (km/h)"]]
    )

    st.subheader("Risk Score Comparison (0–1)")

    st.bar_chart(
    analytics_df.set_index(
        "Vehicle"
    )[["Risk Score"]]
)


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "MINESAFE • Smart Mining Safety Monitoring System • "
    "DEMO MODE — Sensor/GNSS values are simulated until "
    "ESP32 integration."
)


# =========================================================
# AUTO REFRESH
# =========================================================

time.sleep(2)
st.rerun()