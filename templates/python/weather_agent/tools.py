"""Tool definitions for Google ADK & Material A2UI Agent."""

from typing import Any, Dict


def get_current_weather(city: str) -> Dict[str, Any]:
    """Retrieves the current weather information for a specified city.

    Args:
        city: The name of the city (e.g., 'Delhi', 'Kolkata', 'Hyderabad', 'Bengaluru').

    Returns:
        A dictionary with the temperature, conditions, humidity, and wind speed.
    """
    normalized_city = city.strip().lower()
    weather_database = {
        "delhi": {
            "temperature": "18°C (64°F)",
            "condition": "Partly Cloudy with Fog",
            "humidity": "74%",
            "wind": "15 km/h W",
        },
        "kolkata": {
            "temperature": "22°C (72°F)",
            "condition": "Sunny and Clear",
            "humidity": "52%",
            "wind": "11 km/h NE",
        },
        "hyderabad": {
            "temperature": "15°C (59°F)",
            "condition": "Light Drizzle",
            "humidity": "82%",
            "wind": "18 km/h SW",
        },
        "bengaluru": {
            "temperature": "27°C (81°F)",
            "condition": "Pleasant and Breezy",
            "humidity": "64%",
            "wind": "13 km/h E",
        },
    }

    report = weather_database.get(
        normalized_city,
        {
            "temperature": "21°C (70°F)",
            "condition": "Sunny & Mild",
            "humidity": "60%",
            "wind": "10 km/h",
        },
    )

    return {
        "status": "success",
        "city": city.strip().title(),
        **report,
    }


__all__ = ["get_current_weather"]
