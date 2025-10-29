import requests
import json

def test_gemini_api():
    """Test the Gemini API functionality"""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyB429IPSVybUKLFsmDtIuCCMVe80kMZ18Y"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    test_address = "SHOP NO 6&7 MISAL PRIDE, Bagal Chowk, Shahu Mill Rd, Poorvarang, Mahalaxminagar, Rajarampuri, Kolhapur, Maharashtra 416008, India"
    prompt = f"Extract only the city or town name from the following address. Return only the city/town name, nothing else.\n\nAddress: {test_address}"
    
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
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print("API Response Status: Success")
        print("Full Response:", json.dumps(result, indent=2))
        
        if 'candidates' in result and len(result['candidates']) > 0:
            parts = result['candidates'][0]['content']['parts']
            if len(parts) > 0 and 'text' in parts[0]:
                city = parts[0]['text'].strip()
                print(f"\nExtracted City: {city}")
            else:
                print("No text part found in response")
        else:
            print("No candidates found in response")
    else:
        print(f"API Response Status: Failed (Status Code: {response.status_code})")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_gemini_api()