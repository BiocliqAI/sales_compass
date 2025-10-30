
import os
import pandas as pd
import requests
import json
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List

# Database setup - use environment variable or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ct_scan_centers.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy model
class CTScanCenter(Base):
    __tablename__ = "ct_scan_centers"
    id = Column(Integer, primary_key=True, index=True)
    center_name = Column(String, index=True)
    address = Column(String)
    contact_details = Column(String)
    google_maps_link = Column(String)
    city = Column(String, index=True)
    validated = Column(Boolean, default=False)  # New field to track if city data is validated

Base.metadata.create_all(bind=engine)

# Pydantic schema
class CTScanCenterSchema(BaseModel):
    id: int
    center_name: str
    address: str
    contact_details: str
    google_maps_link: str
    city: str
    validated: bool

    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes for Pydantic V2

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_city_from_gemini(address):
    """Extract city/town from address using Gemini API"""
    if not address:
        return "Unknown"
    
    try:
        # Get API key from environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("GEMINI_API_KEY environment variable not set")
            return extract_city_from_address(address)
        
        # Gemini API endpoint for text generation
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
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
            # If API fails, use fallback method
            print(f"Gemini API request failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        # If there's an error, use fallback method
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
        "Parbhani", "Jalna", "Aurangabad", "Osmanabad", "Nanded",
        "Latur", "Solapur", "Pune", "Mumbai", "Nagpur", "Amravati"
    ]
    
    address_lower = address.lower()
    
    # Look for city names in the address
    for city in cities:
        if city.lower() in address_lower:
            return city
    
    # If no city is found, return "Unknown"
    return "Unknown"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def load_initial_data():
    db = SessionLocal()
    if db.query(CTScanCenter).count() == 0:
        data_files = [f for f in os.listdir("..") if f.endswith(".csv")]
        for file_name in data_files:
            df = pd.read_csv(os.path.join("..", file_name))
            for _, row in df.iterrows():
                city = get_city_from_gemini(row["Address"])
                center = CTScanCenter(
                    center_name=row["Center Name"],
                    address=row["Address"],
                    contact_details=row["Contact Details"],
                    google_maps_link=row["Google Maps Link"],
                    city=city,
                    validated=False  # Add the new validated field with default value
                )
                db.add(center)
        db.commit()
    db.close()

@app.get("/api/centers", response_model=List[CTScanCenterSchema])
def get_centers(db: Session = Depends(get_db)):
    return db.query(CTScanCenter).all()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    df = pd.read_csv(file.file)
    for _, row in df.iterrows():
        city = get_city_from_gemini(row["Address"])
        center = CTScanCenter(
            center_name=row["Center Name"],
            address=row["Address"],
            contact_details=row["Contact Details"],
            google_maps_link=row["Google Maps Link"],
            city=city,
        )
        db.add(center)
    db.commit()
    return {"message": "File uploaded and data added successfully"}

@app.delete("/api/deduplicate")
def remove_duplicates(db: Session = Depends(get_db)):
    # Get all centers ordered by id
    all_centers = db.query(CTScanCenter).order_by(CTScanCenter.id).all()
    
    # Create a dictionary to track addresses we've seen
    seen_addresses = set()
    duplicates_to_remove = []
    
    for center in all_centers:
        # Normalize the address for comparison (trim whitespace and convert to lowercase)
        normalized_address = center.address.strip().lower() if center.address else ""
        
        if normalized_address in seen_addresses:
            # This is a duplicate based on address
            duplicates_to_remove.append(center.id)
        else:
            # Add this address to our set of seen addresses
            seen_addresses.add(normalized_address)
    
    # Remove the duplicates from the database
    if duplicates_to_remove:
        db.query(CTScanCenter).filter(CTScanCenter.id.in_(duplicates_to_remove)).delete()
        db.commit()
        
    return {
        "message": f"Removed {len(duplicates_to_remove)} duplicate records",
        "duplicates_removed": len(duplicates_to_remove)
    }


@app.post("/api/update-cities")
def update_all_cities(db: Session = Depends(get_db)):
    """Update all existing records with cities extracted from their addresses using Gemini API"""
    all_centers = db.query(CTScanCenter).all()
    
    updated_count = 0
    for center in all_centers:
        # Extract city using Gemini API
        new_city = get_city_from_gemini(center.address)
        
        # Only update if the city has changed
        if center.city != new_city:
            center.city = new_city
            updated_count += 1
    
    # Commit all changes to the database
    db.commit()
    
    return {
        "message": f"Updated {updated_count} records with new city names from Gemini API",
        "total_processed": len(all_centers),
        "cities_updated": updated_count
    }


@app.delete("/api/centers/{center_id}")
def delete_center(center_id: int, db: Session = Depends(get_db)):
    """Delete a specific center by ID"""
    center = db.query(CTScanCenter).filter(CTScanCenter.id == center_id).first()
    
    if not center:
        return {"error": "Center not found"}
    
    db.delete(center)
    db.commit()
    
    return {"message": f"Center with ID {center_id} has been deleted successfully"}


@app.put("/api/cities/{city_name}/validate")
def update_city_validation(city_name: str, validated: bool, db: Session = Depends(get_db)):
    """Update validation status for all centers in a specific city"""
    centers = db.query(CTScanCenter).filter(CTScanCenter.city == city_name).all()
    
    if not centers:
        return {"error": f"No centers found for city {city_name}"}
    
    for center in centers:
        center.validated = validated
    
    db.commit()
    
    return {"message": f"Updated validation status for all centers in {city_name} to {validated}"}


@app.get("/api/cities/stats")
def get_city_stats(db: Session = Depends(get_db)):
    """Get statistics about cities and centers"""
    from sqlalchemy import func
    
    # Get city counts
    city_counts = db.query(CTScanCenter.city, func.count(CTScanCenter.id).label('count')).group_by(CTScanCenter.city).all()
    
    # Get total centers
    total_centers = db.query(CTScanCenter).count()
    
    # Get cities with validation status
    validated_cities = db.query(CTScanCenter.city).filter(CTScanCenter.validated == True).distinct().count()
    
    return {
        "total_centers": total_centers,
        "cities_count": len(city_counts),
        "validated_cities": validated_cities,
        "city_distribution": [{"city": row[0], "count": row[1]} for row in city_counts]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)
