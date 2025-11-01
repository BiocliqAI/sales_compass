import os
import re
import json
from typing import Tuple, Optional

import requests

# A mapping of state names to their canonical form.
_STATE_CANONICAL = {
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chandigarh": "Chandigarh",
    "chhattisgarh": "Chhattisgarh",
    "dadra and nagar haveli": "Dadra and Nagar Haveli",
    "daman and diu": "Daman and Diu",
    "delhi": "Delhi",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "jammu and kashmir": "Jammu and Kashmir",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "ladakh": "Ladakh",
    "lakshadweep": "Lakshadweep",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "puducherry": "Puducherry",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "uttaranchal": "Uttarakhand",
    "west bengal": "West Bengal",
}


def _normalise_state_name(candidate: str) -> str:
    """Normalise Gemini responses into canonical Indian state names."""
    if not candidate:
        return ""

    cleaned = candidate.strip()
    if not cleaned:
        return ""

    lowered = cleaned.lower()
    if lowered in {"unknown", "unknown state", "not sure", "cannot determine"}:
        return ""

    cleaned = re.sub(r"(?i)\b(state|union territory|ut)\b", "", cleaned)
    cleaned = re.sub(r"[^A-Za-z\s&-]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    lowered = cleaned.lower()

    if lowered in _STATE_CANONICAL:
        return _STATE_CANONICAL[lowered]

    # Handle cases like "Delhi NCR" by keeping the cleaned text
    return cleaned.title() if cleaned else ""


def get_city_and_state_from_address(address: str) -> Tuple[str, str]:
    """
    Extracts the city and state from a given address using the Gemini API.

    Args:
        address: The full address string.

    Returns:
        A tuple containing the city and state.
        Returns ("Unknown", "Unknown State") if extraction fails.
    """
    if not address or not address.strip():
        return "Unknown", "Unknown State"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set")
        return "Unknown", "Unknown State"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    prompt = f"""
    From the following Indian address, extract the city and state.
    Return the response as a JSON object with two keys: "city" and "state".
    If you cannot determine the city or state, use the value "Unknown".

    Address: "{address}"
    """

    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
        },
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.RequestException as exc:
        print(f"Error calling Gemini API for address extraction: {exc}")
        return "Unknown", "Unknown State"

    try:
        payload = response.json()
        content = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
        result = json.loads(content)
        
        city = result.get("city", "Unknown").strip()
        state = result.get("state", "Unknown State").strip()

        # Normalize the state name for consistency
        normalized_state = _normalise_state_name(state)

        return city or "Unknown", normalized_state or "Unknown State"

    except (ValueError, IndexError, json.JSONDecodeError) as exc:
        print(f"Gemini API returned an invalid response: {exc}")
        return "Unknown", "Unknown State"