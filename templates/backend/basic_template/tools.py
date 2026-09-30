# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Hotel Portfolio Manager Agent Tools."""
import collections
import datetime
import json
import random
from typing import List

from . import viz

random.seed(7)

# --- Mock Data ---

MANAGERS = [
    {"manager_id": "mgr_01", "name": "Ava Chen", "phone": "+44 20 7946 0958", "photo_url": "https://i.pravatar.cc/150?u=mgr_01"},
    {"manager_id": "mgr_02", "name": "Ben Carter", "phone": "+44 20 7946 0959", "photo_url": "https://i.pravatar.cc/150?u=mgr_02"},
    {"manager_id": "mgr_03", "name": "Chloe Davis", "phone": "+33 1 82 88 47 31", "photo_url": "https://i.pravatar.cc/150?u=mgr_03"},
    {"manager_id": "mgr_04", "name": "David Evans", "phone": "+33 1 82 88 47_32", "photo_url": "https://i.pravatar.cc/150?u=mgr_04"},
    {"manager_id": "mgr_05", "name": "Eva Fernandez", "phone": "+34 931 81 67 89", "photo_url": "https://i.pravatar.cc/150?u=mgr_05"},
    {"manager_id": "mgr_06", "name": "Frank Garcia", "phone": "+34 931 81 67 90", "photo_url": "https://i.pravatar.cc/150?u=mgr_06"},
    {"manager_id": "mgr_07", "name": "Grace Hughes", "phone": "+351 21 123 4567", "photo_url": "https://i.pravatar.cc/150?u=mgr_07"},
    {"manager_id": "mgr_08", "name": "Henry Irving", "phone": "+351 21 123 4568", "photo_url": "https://i.pravatar.cc/150?u=mgr_08"},
]

HOTELS = [
    {"hotel_id": "hotel_01", "name": "The Londoner", "city": "London", "lat": 51.509865, "lng": -0.118092, "manager_id": "mgr_01"},
    {"hotel_id": "hotel_02", "name": "Thames View", "city": "London", "lat": 51.505, "lng": -0.075, "manager_id": "mgr_02"},
    {"hotel_id": "hotel_03", "name": "Le Marais Charm", "city": "Paris", "lat": 48.8566, "lng": 2.3522, "manager_id": "mgr_03"},
    {"hotel_id": "hotel_04", "name": "Eiffel Dream", "city": "Paris", "lat": 48.8584, "lng": 2.2945, "manager_id": "mgr_04"},
    {"hotel_id": "hotel_05", "name": "Gothic Quarter", "city": "Barcelona", "lat": 41.3851, "lng": 2.1734, "manager_id": "mgr_05"},
    {"hotel_id": "hotel_06", "name": "Playa Barceloneta", "city": "Barcelona", "lat": 41.380, "lng": 2.188, "manager_id": "mgr_06"},
    {"hotel_id": "hotel_07", "name": "Lisbon Historic", "city": "Lisbon", "lat": 38.7223, "lng": -9.1393, "manager_id": "mgr_07"},
    {"hotel_id": "hotel_08", "name": "Tagus Riverfront", "city": "Lisbon", "lat": 38.707, "lng": -9.135, "manager_id": "mgr_08"},
]

AMENITIES = ["Free WiFi", "Pool", "Gym", "Restaurant", "Bar", "Spa", "Pet Friendly", "Parking"]
ROLES = ["Front Desk", "Concierge", "Housekeeping", "Maintenance", "Chef", "Bartender"]
ROOM_TYPES = [
    {"type": "Standard Queen", "max_guests": 2},
    {"type": "Deluxe King", "max_guests": 2},
    {"type": "Family Suite", "max_guests": 4},
    {"type": "Rooftop Penthouse", "max_guests": 2},
]

HOTEL_DATA = {}
for hotel in HOTELS:
    manager = next(m for m in MANAGERS if m["manager_id"] == hotel["manager_id"])
    adr = random.randint(150, 450)
    occupancy = random.randint(65, 98)
    HOTEL_DATA[hotel["hotel_id"]] = {
        **hotel,
        **manager,
        "name": hotel["name"],            
        "manager_name": manager["name"],
        "stars": random.randint(3, 5),
        "rooms": random.randint(50, 150),
        "occupancy_pct": occupancy,
        "adr_eur": adr,
        "revpar_eur": int(adr * (occupancy / 100)),
        "guest_rating": round(random.uniform(3.8, 4.9), 1),
        "amenities": sorted(random.sample(AMENITIES, k=random.randint(3, 5))),
        "image_url": f"https://picsum.photos/seed/{hotel['hotel_id']}/800/500",
        "reviews": [
            {"date": (datetime.date.today() - datetime.timedelta(days=random.randint(1, 60))).isoformat(), "guest": f"Guest {random.randint(100, 999)}", "rating": random.randint(3, 5), "comment": "A wonderful stay, highly recommend."} for _ in range(8)
        ],
        "staff": [
             {"name": f"Staff {i+1}", "role": random.choice(ROLES), "photo_url": f"https://i.pravatar.cc/150?u=staff_{hotel['hotel_id']}_{i}"} for i in range(random.randint(4, 8))
        ],
        "room_rates": [
            {"room_type": rt["type"], "max_guests": rt["max_guests"], "rate_eur": random.randint(100, 300) * (i+1), "available_rooms": random.randint(0, 10)} for i, rt in enumerate(ROOM_TYPES)
        ],
        "occupancy_trend": sorted([random.randint(50, 99) for _ in range(12)]),
        "occupancy_last_year": sorted([random.randint(45, 95) for _ in range(12)]),
    }


def get_hotels() -> dict:
    """Retrieves the list of all hotels for the portfolio gallery or to populate a form picker."""
    rows = [
        {
            "hotel_id": d["hotel_id"],
            "name": d["name"],
            "city": d["city"],
            "stars": d["stars"],
            "rooms": d["rooms"],
            "occupancy_pct": d["occupancy_pct"],
            "adr_eur": d["adr_eur"],
            "image_url": d["image_url"],
            "manager_name": d["manager_name"],
            "manager_phone": d["phone"],
            "manager_photo_url": d["photo_url"],
            "amenities_str": ", ".join(d["amenities"]),
        } for d in HOTEL_DATA.values()
    ]
    return {"status": "success", "rows": rows}


def get_hotel_dashboard(hotel_id: str) -> dict:
    """Retrieves all data needed for a single hotel's detailed dashboard."""
    if hotel_id not in HOTEL_DATA:
        return {"status": "error", "error": "Hotel not found."}
    data = HOTEL_DATA[hotel_id]

    # KPI grid data
    kpis = [
        {"label": "ADR", "value": data["adr_eur"], "unit": "EUR"},
        {"label": "RevPAR", "value": data["revpar_eur"], "unit": "EUR"},
        {"label": "Occupancy", "value": data["occupancy_pct"], "unit": "%"},
        {"label": "Guest Rating", "value": data["guest_rating"], "unit": "/ 5"},
    ]

    # Occupancy trend chart data
    months = [f"M-{i}" for i in range(12, 0, -1)]
    occupancy_rows = []
    for i, month in enumerate(months):
        occupancy_rows.append({"month": month, "period": "This Year", "occupancy": data["occupancy_trend"][i]})
        occupancy_rows.append({"month": month, "period": "Last Year", "occupancy": data["occupancy_last_year"][i]})

    try:
        plot_path = viz.save_chart(occupancy_rows, "line", x="month", y="occupancy", color="period", y_title="Occupancy %")
    except ValueError as exc:
        return {"status": "error", "error": str(exc)}

    return {
        "status": "success",
        "hotel_id": data["hotel_id"],
        "name": data["name"],
        "city": data["city"],
        "image_url": data["image_url"],
        "kpis": {"rows": kpis},
        "occupancy_plot_path": plot_path,
        "reviews": {"rows": data["reviews"]},
        "staff": {"rows": data["staff"]},
    }

def get_revenue_by_city() -> dict:
    """Aggregates hotel portfolio revenue by city for a chart."""
    city_revenue = collections.defaultdict(int)
    for data in HOTEL_DATA.values():
        revenue = data["revpar_eur"] * data["rooms"] * 30  # Monthly estimate
        city_revenue[data["city"]] += revenue
    rows = [{"city": city, "revenue": rev} for city, rev in city_revenue.items()]
    return {"status": "success", "rows": rows}


def get_hotel_map() -> dict:
    """Generates a map of all hotel locations."""
    points = [{"name": d["name"], "city": d["city"], "lat": d["lat"], "lng": d["lng"]} for d in HOTEL_DATA.values()]
    try:
        plot_path = viz.save_map(points, label="name", color="city")
    except ValueError as exc:
        return {"status": "error", "error": str(exc)}
    
    rows = [{"hotel": p["name"], "city": p["city"], "lat": p["lat"], "lng": p["lng"]} for p in points]
    result = {"status": "success", "plot_path": plot_path, "rows": rows}
    map_path = viz.save_google_map(points)
    if map_path:
        result["map_path"] = map_path
    return result

def get_room_rates(hotel_id: str) -> dict:
    """Retrieves room rate information for a specific hotel."""
    if hotel_id not in HOTEL_DATA:
        return {"status": "error", "error": "Hotel not found."}
    return {"status": "success", "hotel_id": hotel_id, "rows": HOTEL_DATA[hotel_id]["room_rates"]}

def save_room_rates(hotel_id: str, rows: List[dict]) -> dict:
    """Saves updated room rate values from the editable table."""
    if hotel_id not in HOTEL_DATA:
        return {"status": "error", "error": "Hotel not found."}

    if isinstance(rows, str):
        try:
            rows = json.loads(rows)
        except json.JSONDecodeError:
            return {"status": "error", "error": "Edited rows could not be read."}
    if not isinstance(rows, list):
        return {"status": "error", "error": "No table rows were received."}

    # In a real app, this would save to a database. Here we just return them.
    return {"status": "saved", "hotel_id": hotel_id, "rows": rows}

def submit_maintenance_request(
    hotel_id: str,
    category: str,
    priority: str,
    description: str,
    estimated_cost_eur: int = 0,
    due_date: str = "",
    notify_manager: bool = False,
) -> dict:
    """Processes a new maintenance request form."""
    # ChoicePicker values can be lists, normalize them
    if isinstance(hotel_id, list): hotel_id = hotel_id[0] if hotel_id else ""
    if isinstance(category, list): category = category[0] if category else ""
    if isinstance(priority, list): priority = priority[0] if priority else ""

    if not all([hotel_id, category, description]):
        return {"status": "error", "error": "Hotel, Category, and Description are required."}

    hotel_info = HOTEL_DATA.get(hotel_id, {})
    return {
        "status": "submitted",
        "hotel_name": hotel_info.get("name", "N/A"),
        "hotel_image_url": hotel_info.get("image_url", ""),
        "category": category,
        "priority": priority,
        "description": description,
        "estimated_cost_eur": estimated_cost_eur,
        "due_date": due_date[:10] if due_date else "Not specified",
        "notify_manager": "Yes" if notify_manager else "No",
    }

def restart_flow() -> dict:
    """Passthrough tool to signal a UI reset to the welcome screen."""
    return {"status": "restarted"}