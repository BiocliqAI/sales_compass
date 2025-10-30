import requests
import json
import sqlite3

from city_utils import extract_city_from_address as extract_city_from_address_util

def get_city_from_gemini(address):
    """Extract city/town from address using Gemini API"""
    if not address or address.strip().lower() == "india":
        return "Unknown"
    
    try:
        # Gemini API endpoint for text generation
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyB429IPSVybUKLFsmDtIuCCMVe80kMZ18Y"
        
        # Prepare the request payload
        headers = {
            'Content-Type': 'application/json'
        }
        
        prompt = f"Extract only the city or town name from the following address. Return only the city/town name, nothing else.\n\nAddress: {address}"
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 20
            }
        }
        
        # Make the API request
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            # Extract the city name from the response
            if 'candidates' in result and len(result['candidates']) > 0:
                parts = result['candidates'][0]['content']['parts']
                if len(parts) > 0 and 'text' in parts[0]:
                    city = parts[0]['text'].strip()
                    # Clean up any extra text or formatting
                    city = city.replace('\n', '').strip()
                    # Handle special cases where Gemini returns non-city responses
                    if city.lower() in ["india is a country, not a city or town. i cannot extract a city or town name from", 
                                        "india is a country, not a city or town. i cannot extract a city or town name from this text."]:
                        return "Unknown"
                    return city
        else:
            print(f"Gemini API request failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
    
    # Fallback to local extraction if API fails
    return extract_city_from_address(address)


def extract_city_from_address(address):
    """Extract city name from address field - fallback method"""
    return extract_city_from_address_util(address)


# Connect to the database
conn = sqlite3.connect('./ct_scan_centers.db')
cursor = conn.cursor()

# Get all centers with Unknown city
cursor.execute("SELECT id, address FROM ct_scan_centers WHERE city = 'Unknown'")
unknown_centers = cursor.fetchall()

print(f"Found {len(unknown_centers)} centers with Unknown city")

# Process each center
updated_count = 0
for center_id, address in unknown_centers:
    # Skip empty addresses or just "India"
    if not address or address.strip().lower() == "india":
        continue
        
    # Try to extract city using Gemini API first
    city = get_city_from_gemini(address)
    
    # If Gemini API fails, try local extraction
    if city == "Unknown":
        city = extract_city_from_address(address)
    
    # Update the record if we found a city
    if city != "Unknown":
        cursor.execute("UPDATE ct_scan_centers SET city = ? WHERE id = ?", (city, center_id))
        print(f"Updated center {center_id}: {address[:50]}... -> {city}")
        updated_count += 1

# Commit changes and close connection
conn.commit()
conn.close()

print(f"Updated {updated_count} centers with new city names")
