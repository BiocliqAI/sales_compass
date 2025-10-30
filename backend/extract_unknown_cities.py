import requests
import json
import sqlite3

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
    if not address or address.strip().lower() == "india":
        return "Unknown"
    
    # Extended list of common cities found in the dataset
    cities = [
        "Kolhapur", "Jalgaon", "Aurangabad", "Nagpur", "Nashik", 
        "Pune", "Mumbai", "Ahmednagar", "Latur", "Beed", "Sangli",
        "Satara", "Sindhudurg", "Ratnagiri", "Raigad", "Thane",
        "Bhandara", "Gondia", "Chandrapur", "Yavatmal", "Wardha",
        "Amravati", "Akola", "Buldhana", "Washim", "Hingoli",
        "Parbhani", "Jalna", "Aurangabad", "Osmanabad", "Nanded",
        "Latur", "Solapur", "Pune", "Mumbai", "Nagpur", "Amravati",
        "Jaysingpur", "Shirpur", "Chopda", "Ichalkaranji", "Kagal",
        "Kopargaon", "Kudal", "Miraj", "Mira Bhayandar", "Navi Mumbai",
        "Pachora", "Palus", "Parli", "Pathardi", "Sangamner",
        "Shirdi", "Shirur", "Tasgaon", "Uran", "Vaijapur",
        "Vasai-Virar", "Wardha", "Yavatmal", "Amalner", "Baramati",
        "Barshi", "Chinchwad", "Dehu Road", "Hadapsar", "Hinjewadi",
        "Jejuri", "Khadkale", "Khed", "Lonavala", "Mhaswad",
        "Pimpri-Chinchwad", "Sangli-Miraj-Kupwad", "Shikrapur", "Vadgaon",
        "Vadodara", "Ambajogai", "Ashti", "Bhadravati", "Darwha",
        "Deglur", "Gadhinglaj", "Hatkanangle", "Islampur", "Jath",
        "Kankavli", "Karad", "Khadkoli", "Khatav", "Koregaon",
        "Madangad", "Mahabaleshwar", "Mahad", "Malegaon", "Malwan",
        "Manchar", "Mangaon", "Mangrulpir", "Mhasla", "Moschi",
        "Muktainagar", "Narayangaon", "Nigdi", "Niphad", "Ozar",
        "Pandharpur", "Pen", "Phaltan", "Sangameshwar", "Sangamner",
        "Shirgaon", "Sillod", "Sindhudurg", "Talegaon Dabhade", "Tarapur",
        "Vita", "Wai", "Walchandnagar", "Warora", "Yaval",
        "Kadamwadi", "Kawala Naka", "Gandhinagar", "Ajara", "Shahu Mill Rd",
        "Poorvarang", "Mahalaxminagar", "Rajarampuri", "Ujalaiwadi",
        "Kadamwadi - Jadhavwadi Rd", "E Ward", "Scheme No.4", "Laxminarayan Nagar",
        "Kadamwadi", "Shahupuri", "Mumbai - Pune Hwy", "Kavlapur", "New Usmanpura",
        "Chhatrapati Sambhajinagar", "Ahilyanagar", "Bhusawal", "Chalisgaon",
        "Apte Colony", "Lakshmi Rd", "Patil Mala", "Shirol wadi road",
        "K K Zenith Building", "S T Stand", "Laxmi Nagar", "Bhaskar Market Rd",
        "Pratap Nagar", "Ganesh Nagar", "Devidas Colony", "Ranchos Nagar",
        "Suyog Society", "Shivaji Nagar", "Bhadgaon", "Dahegaon", "Kusgaon Budruk",
        "Mira Bhayander", "Nerul", "Vashi", "Belapur", "Panvel",
        "Khopoli", "Butibori", "Wanadongri", "Hingna", "Katol",
        "Saoner", "Kalmeshwar", "Kamptee", "Koradi", "Umred",
        "Kuhi", "Parseoni", "Ramtek", "Mauda", "Kalmana",
        "Seloo", "Wardha", "Hinganghat", "Deoli", "Arvi",
        "Pulgaon", "Risod", "Ghatanji", "Yavatmal", "Darwha",
        "Digras", "Pusad", "Kalamb", "Maregaon", "Babhulgaon",
        "Wani", "Jat", "Kelapur", "Mahagaon", "Mangrulpir",
        "Zari", "Jamkhed", "Karjat", "Pathardi", "Shrigonda",
        "Parner", "Akole", "Sangamner", "Kopargaon", "Shirdi",
        "Newasa", "Rahuri", "Nagar", "Shevgaon", "Shrirampur",
        "Nevasa", "Phaltan", "Wai", "Man", "Khandala",
        "Bhor", "Ambegaon", "Indapur", "Baramati", "Purandhar",
        "Velhe", "Daund", "Junnar", "Alephata", "Khed",
        "Mhaswad", "Akkalkot", "South Solapur", "Pandharpur", "Sangole",
        "Barshi", "Mohol", "Madha", "Solapur", "Karmala",
        "Malshiras", "Sangli", "Atpadi", "Jat", "Shirala",
        "Palus", "Kadegaon", "Sangli-Miraj-Kupwad", "Tasgaon", "Vita",
        "Kavath", "Ichalkaranji", "Walwa", "Jaysingpur", "Kagal",
        "Hatkanangale", "Shirol", "Gadhinglaj", "Ajara", "Sindhudurg",
        "Kudal", "Sawantwadi", "Deogad", "Malwan", "Vengurla",
        "Kankavli", "Vaibhavwadi", "Ratnagiri", "Sangameshwar", "Chiplun",
        "Guhagar", "Mandangad", "Dapoli", "Khed", "Lanja",
        "Rajapur", "Shirgaon", "Nagothane", "Pen", "Alibag",
        "Murud", "Rewas", "Mangaon", "Tala", "Mahad",
        "Poladpur", "Pali", "Neral", "Bhira", "Mhasla",
        "Shrivardhan", "Khopoli", "Lonavala", "Khandala", "Talegaon Dabhade",
        "Chakan", "Charholi", "Dopatta", "Pimpri-Chinchwad", "Pune",
        "Hinjewadi", "Wakad", "Balewadi", "Baner", "Aundh",
        "Kothrud", "Warje", "Hadapsar", "Katraj", "Viman Nagar",
        "Yerwada", "Dhole Patil Road", "Shivaji Nagar", "Camp", "Deccan Gymkhana",
        "Erandwane", "Model Colony", "JM Road", "FC Road", "Law College Road",
        "University Road", "Ganeshkhind", "Aundh Road", "Bund Garden Road", "MG Road",
        "Boat Club Road", "Sion", "Dadar", "Bandra", "Andheri",
        "Juhu", "Versova", "Malad", "Goregaon", "Kandivali",
        "Borivali", "Dahisar", "Vasai", "Virar", "Nallasopara",
        "Vasai-Virar", "Palghar", "Dahanu", "Vikramgad", "Jawhar",
        "Talasari", "Mokhada", "Shahapur", "Wada", "Thane",
        "Ulhasnagar", "Kalyan", "Dombivli", "Ambernath", "Badlapur",
        "Vitthalwadi", "Kalwa", "Mumbra", "Turbhe", "Kopar Khairane",
        "Ghansoli", "Airoli", "Rabale", "Vashi", "Nerul",
        "Juinagar", "Turbhe", "Belapur CBD", "Kharghar", "Seawoods",
        "Dombivli East", "Kopar", "Divya Shakti Township", "Shilphata", "Ambarnath",
        "Ulwe", "Taloja", "Kalamboli", "Panvel", "Kamothe",
        "Vashi", "Nerul", "Seawoods", "Belapur", "Kharghar",
        "Airoli", "Ghansoli", "Rabale", "Kopar Khairane", "Turbhe",
        "Juinagar", "Navi Mumbai", "Mumbai", "Pune", "Nagpur",
        "Nashik", "Aurangabad", "Solapur", "Amravati", "Kolhapur",
        "Sangli", "Satara", "Latur", "Ahmednagar", "Akola",
        "Jalgaon", "Parbhani", "Beed", "Jalna", "Osmanabad",
        "Nanded", "Wardha", "Chandrapur", "Yavatmal", "Bhandara",
        "Gondia", "Washim", "Hingoli", "Buldhana", "Amalner",
        "Chopda", "Bhusawal", "Raver", "Muktainagar", "Yawal",
        "Chalisgaon", "Pachora", "Jamner", "Bodwad", "Erandol",
        "Dharangaon", "Pathri", "Shrigonda", "Parner", "Akole",
        "Sangamner", "Kopargaon", "Shirdi", "Newasa", "Rahuri",
        "Nagar", "Shevgaon", "Shrirampur", "Nevasa", "Phaltan",
        "Wai", "Man", "Khandala", "Bhor", "Ambegaon",
        "Indapur", "Baramati", "Purandhar", "Velhe", "Daund",
        "Junnar", "Alephata", "Mhaswad", "Akkalkot", "South Solapur",
        "Pandharpur", "Sangole", "Barshi", "Mohol", "Madha",
        "Karmala", "Malshiras", "Atpadi", "Shirala", "Palus",
        "Kadegaon", "Tasgaon", "Vita", "Kavath", "Ichalkaranji",
        "Walwa", "Jaysingpur", "Kagal", "Hatkanangale", "Shirol",
        "Gadhinglaj", "Ajara", "Kudal", "Sawantwadi", "Deogad",
        "Vengurla", "Kankavli", "Vaibhavwadi", "Chiplun", "Guhagar",
        "Mandangad", "Dapoli", "Lanja", "Rajapur", "Shirgaon",
        "Nagothane", "Pen", "Alibag", "Murud", "Rewas",
        "Mangaon", "Tala", "Mahad", "Poladpur", "Pali",
        "Neral", "Bhira", "Mhasla", "Shrivardhan", "Khopoli",
        "Lonavala", "Talegaon Dabhade", "Chakan", "Charholi", "Dopatta",
        "Hinjewadi", "Wakad", "Balewadi", "Baner", "Aundh",
        "Kothrud", "Warje", "Hadapsar", "Katraj", "Viman Nagar",
        "Yerwada", "Dhole Patil Road", "Shivaji Nagar", "Camp", "Deccan Gymkhana",
        "Erandwane", "Model Colony", "JM Road", "FC Road", "Law College Road",
        "University Road", "Ganeshkhind", "Aundh Road", "Bund Garden Road", "MG Road",
        "Boat Club Road", "Sion", "Dadar", "Bandra", "Andheri",
        "Juhu", "Versova", "Malad", "Goregaon", "Kandivali",
        "Borivali", "Dahisar", "Vasai", "Virar", "Nallasopara",
        "Palghar", "Dahanu", "Vikramgad", "Jawhar", "Talasari",
        "Mokhada", "Shahapur", "Wada", "Ulhasnagar", "Kalyan",
        "Dombivli", "Ambernath", "Badlapur", "Vitthalwadi", "Kalwa",
        "Mumbra", "Turbhe", "Seawoods", "Dombivli East", "Kopar",
        "Divya Shakti Township", "Shilphata", "Ulwe", "Taloja", "Kalamboli",
        "Panvel", "Kamothe", "Belapur CBD", "Kharghar", "Airoli",
        "Ghansoli", "Rabale", "Vashi", "Nerul", "Juinagar",
        "Turbhe", "Navi Mumbai", "Mumbai", "Pune", "Nagpur",
        "Nashik", "Aurangabad", "Solapur", "Amravati", "Kolhapur",
        "Sangli", "Satara", "Latur", "Ahmednagar", "Akola",
        "Jalgaon", "Parbhani", "Beed", "Jalna", "Osmanabad",
        "Nanded", "Wardha", "Chandrapur", "Yavatmal", "Bhandara",
        "Gondia", "Washim", "Hingoli", "Buldhana", "Amalner",
        "Chopda", "Bhusawal", "Raver", "Muktainagar", "Yawal",
        "Chalisgaon", "Pachora", "Jamner", "Bodwad", "Erandol",
        "Dharangaon", "Pathri", "Shrigonda", "Parner", "Akole",
        "Sangamner", "Kopargaon", "Shirdi", "Newasa", "Rahuri",
        "Nagar", "Shevgaon", "Shrirampur", "Nevasa", "Phaltan",
        "Wai", "Man", "Khandala", "Bhor", "Ambegaon",
        "Indapur", "Baramati", "Purandhar", "Velhe", "Daund",
        "Junnar", "Alephata", "Sillod", "Mangrulpir", "Kalamnuri",
        "Sonbhadra", "Barshi", "Mohol", "Madha", "Karmala",
        "Malshiras", "Atpadi", "Shirala", "Palus", "Kadegaon",
        "Tasgaon", "Vita", "Kavath", "Ichalkaranji", "Walwa",
        "Jaysingpur", "Kagal", "Hatkanangale", "Shirol", "Gadhinglaj",
        "Ajara", "Kudal", "Sawantwadi", "Deogad", "Vengurla",
        "Kankavli", "Vaibhavwadi", "Chiplun", "Guhagar", "Mandangad",
        "Dapoli", "Lanja", "Rajapur", "Shirgaon", "Nagothane",
        "Pen", "Alibag", "Murud", "Rewas", "Mangaon",
        "Tala", "Mahad", "Poladpur", "Pali", "Neral",
        "Bhira", "Mhasla", "Shrivardhan", "Lonavala", "Talegaon Dabhade",
        "Chakan", "Charholi", "Dopatta", "Hinjewadi", "Wakad",
        "Balewadi", "Baner", "Aundh", "Kothrud", "Warje",
        "Hadapsar", "Katraj", "Viman Nagar", "Yerwada", "Dhole Patil Road",
        "Shivaji Nagar", "Camp", "Deccan Gymkhana", "Erandwane", "Model Colony",
        "JM Road", "FC Road", "Law College Road", "University Road", "Ganeshkhind",
        "Aundh Road", "Bund Garden Road", "MG Road", "Boat Club Road", "Sion",
        "Dadar", "Bandra", "Andheri", "Juhu", "Versova",
        "Malad", "Goregaon", "Kandivali", "Borivali", "Dahisar",
        "Vasai", "Virar", "Nallasopara", "Palghar", "Dahanu",
        "Vikramgad", "Jawhar", "Talasari", "Mokhada", "Shahapur",
        "Wada", "Ulhasnagar", "Kalyan", "Dombivli", "Ambernath",
        "Badlapur", "Vitthalwadi", "Kalwa", "Mumbra", "Turbhe",
        "Seawoods", "Dombivli East", "Kopar", "Divya Shakti Township", "Shilphata",
        "Ulwe", "Taloja", "Kalamboli", "Panvel", "Kamothe",
        "Belapur CBD", "Kharghar", "Airoli", "Ghansoli", "Rabale",
        "Vashi", "Nerul", "Juinagar", "Navi Mumbai", "Mumbai"
    ]
    
    address_lower = address.lower()
    
    # Look for city names in the address
    for city in cities:
        if city.lower() in address_lower:
            # Special handling for some common patterns
            if city.lower() == "kolhapur" and "mahalaxminagar" in address_lower:
                return "Kolhapur"
            elif city.lower() == "pune" and "hinjewadi" in address_lower:
                return "Pune"
            elif city.lower() == "mumbai" and "bandra" in address_lower:
                return "Mumbai"
            else:
                return city
    
    # If no city is found, return "Unknown"
    return "Unknown"


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