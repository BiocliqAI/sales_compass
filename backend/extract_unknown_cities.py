import os
import sqlite3
from typing import Optional

import requests

from city_utils import extract_city_from_address as extract_city_from_address_util


def _load_env_if_needed() -> None:
    """Populate environment variables from a local .env file if GEMINI_API_KEY is unset."""
    if os.getenv("GEMINI_API_KEY"):
        return

    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'\"")
                os.environ.setdefault(key, value)
    except OSError as exc:
        print(f"Warning: could not read .env file ({exc}). Continuing without it.")


def get_city_from_gemini(address: str) -> str:
    """Extract city/town from address using Gemini API when available."""
    if not address or address.strip().lower() == "india":
        return "Unknown"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return extract_city_from_address(address)

    try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={api_key}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Extract only the city or town name from the following address. "
                                "Return only the city/town name, nothing else.\n\n"
                                f"Address: {address}"
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 20,
            },
        }

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            candidates = result.get("candidates") or []
            if not candidates:
                return extract_city_from_address(address)

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return extract_city_from_address(address)

            text: Optional[str] = parts[0].get("text")
            if not text:
                return extract_city_from_address(address)

            city = text.strip().replace("\n", "")
            lowered = city.lower()
            invalid_responses = {
                "india is a country, not a city or town. i cannot extract a city or town name from",
                "india is a country, not a city or town. i cannot extract a city or town name from this text.",
                "india is a country, not a city or town. i cannot extract a city or town name from this address.",
            }
            if lowered in invalid_responses or lowered.startswith(
                "okay, i understand. since you haven't provided an address"
            ):
                return "Unknown"
            return city

        print(f"Gemini API request failed with status {response.status_code}: {response.text}")

    except Exception as exc:  # pylint: disable=broad-except
        print(f"Error calling Gemini API: {exc}")

    return extract_city_from_address(address)


def extract_city_from_address(address: str) -> str:
    """Extract city name from address field - fallback method."""
    return extract_city_from_address_util(address)


def main() -> None:
    _load_env_if_needed()

    conn = sqlite3.connect("./ct_scan_centers.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, address FROM ct_scan_centers WHERE city = 'Unknown'")
    unknown_centers = cursor.fetchall()

    print(f"Found {len(unknown_centers)} centers with Unknown city")

    updated_count = 0
    for center_id, address in unknown_centers:
        if not address or address.strip().lower() == "india":
            continue

        city = get_city_from_gemini(address)
        if city == "Unknown":
            city = extract_city_from_address(address)

        if city != "Unknown":
            cursor.execute("UPDATE ct_scan_centers SET city = ? WHERE id = ?", (city, center_id))
            print(f"Updated center {center_id}: {address[:50]}... -> {city}")
            updated_count += 1

    conn.commit()
    conn.close()

    print(f"Updated {updated_count} centers with new city names")


if __name__ == "__main__":
    main()
