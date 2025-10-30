import requests
import json

def get_city_from_gemini(address):
    """Extract city/town from address using Gemini API"""
    if not address:
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
                    return city
        else:
            print(f"Gemini API request failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
    
    # Fallback to local extraction if API fails
    return extract_city_from_address(address)


def extract_city_from_address(address):
    """Extract city name from address field - fallback method"""
    if not address:
        return "Unknown"
    
    # Common cities found in the dataset
    cities = [
        "Kolhapur", "Jalgaon", "Aurangabad", "Nagpur", "Nashik", 
        "Pune", "Mumbai", "Ahmednagar", "Latur", "Beed", "Sangli",
        "Satara", "Sindhudurg", "Ratnagiri", "Raigad", "Thane",
        "Bhandara", "Gondia", "Chandrapur", "Yavatmal", "Wardha",
        "Amravati", "Akola", "Buldhana", "Washim", "Hingoli",
        "Parbhani", "Jalna", "Osmanabad", "Nanded", "Solapur",
        "Chhatrapati Sambhajinagar", "Ahilyanagar", "Bhusawal", 
        "Chalisgaon", "Chopda", "Ichalkaranji", "Jaysingpur",
        "Kagal", "Kopargaon", "Kudal", "Miraj", "Mira Bhayandar",
        "Navi Mumbai", "Pachora", "Palus", "Parli", "Pathardi",
        "Sangamner", "Shirdi", "Shirpur", "Shrigonda", "Shrirampur",
        "Tasgaon", "Uran", "Vaijapur", "Vasai-Virar", "Wardha",
        "Yavatmal", "Amalner", "Baramati", "Barshi", "Chinchwad",
        "Dehu Road", "Hadapsar", "Hinjewadi", "Jejuri", "Khadkale",
        "Khed", "Lonavala", "Mhaswad", "Pimpri-Chinchwad", 
        "Sangli-Miraj-Kupwad", "Shikrapur", "Vadgaon", "Vadodara"
    ]
    
    address_lower = address.lower()
    
    # Look for city names in the address
    for city in cities:
        if city.lower() in address_lower:
            return city
    
    # If no city is found, return "Unknown"
    return "Unknown"


# Test with the Jaysingpur address
test_address = "Lane no 6, Lakshmi Rd, near by sanjeevan hospital, Patil Mala, Jaysingpur, Maharashtra 416101, India."
result = get_city_from_gemini(test_address)
print(f"Input address: {test_address}")
print(f"Extracted city: {result}")