
import os
import pandas as pd
import requests
import json
from fastapi import FastAPI, File, UploadFile, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Any, Dict, List, Set, Tuple

from city_utils import (
    extract_city_from_address,
    normalize_address_for_dedup,
    normalize_center_name_for_dedup,
)

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
    validated = Column(Boolean, default=False)  # New field to track if center data is validated
    qualified = Column(Boolean, default=False)   # New field to track if center is qualified
    notes = Column(Text, default="")  # Free text notes for each center

Base.metadata.create_all(bind=engine)

def ensure_notes_column():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(ct_scan_centers)"))
        columns = [row[1] for row in result]
        if "notes" not in columns:
            conn.execute(text("ALTER TABLE ct_scan_centers ADD COLUMN notes TEXT DEFAULT ''"))

ensure_notes_column()

# Pydantic schema
class CTScanCenterSchema(BaseModel):
    id: int
    center_name: str
    address: str
    contact_details: str
    google_maps_link: str
    city: str
    validated: bool
    qualified: bool
    notes: str | None

    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes for Pydantic V2


class CTScanCenterUpdateSchema(BaseModel):
    center_name: str
    address: str
    contact_details: str
    google_maps_link: str
    city: str
    validated: bool
    qualified: bool
    notes: str | None = ""


class NotesUpdateSchema(BaseModel):
    notes: str | None = ""

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
                    
                    # Handle special cases where Gemini returns non-city responses
                    if city.lower() in ["india is a country, not a city or town. i cannot extract a city or town name from", 
                                        "india is a country, not a city or town. i cannot extract a city or town name from this text.",
                                        "india is a country, not a city or town. i cannot extract a city or town name from this address."]:
                        return extract_city_from_address(address)
                    
                    return city
        else:
            # If API fails, use fallback method
            print(f"Gemini API request failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        # If there's an error, use fallback method
        print(f"Error calling Gemini API: {str(e)}")
    
    # Fallback to local extraction if API fails
    return extract_city_from_address(address)



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
                notes_value = row.get("Notes", "")
                if pd.isna(notes_value):
                    notes_value = ""
                center = CTScanCenter(
                    center_name=row["Center Name"],
                    address=row["Address"],
                    contact_details=row["Contact Details"],
                    google_maps_link=row["Google Maps Link"],
                    city=city,
                    validated=False,  # Add the new validated field with default value
                    qualified=False,
                    notes=str(notes_value)
                )
                db.add(center)
        db.commit()
    db.close()

@app.get("/api/centers", response_model=List[CTScanCenterSchema])
def get_centers(db: Session = Depends(get_db)):
    return db.query(CTScanCenter).all()


@app.put("/api/centers/{center_id}", response_model=CTScanCenterSchema)
def update_center(center_id: int, center_data: CTScanCenterUpdateSchema, db: Session = Depends(get_db)):
    """Update full center details, including free-text notes."""
    center = db.query(CTScanCenter).filter(CTScanCenter.id == center_id).first()

    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    center.center_name = center_data.center_name.strip()
    center.address = center_data.address.strip()
    center.contact_details = center_data.contact_details.strip()
    center.google_maps_link = center_data.google_maps_link.strip()
    center.city = center_data.city.strip()
    center.validated = center_data.validated
    center.qualified = center_data.qualified
    center.notes = (center_data.notes or "").strip()

    db.commit()
    db.refresh(center)

    return center


@app.patch("/api/centers/{center_id}/notes", response_model=CTScanCenterSchema)
def update_center_notes(center_id: int, notes_payload: NotesUpdateSchema, db: Session = Depends(get_db)):
    """Update only the notes field for a specific center."""
    center = db.query(CTScanCenter).filter(CTScanCenter.id == center_id).first()

    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    center.notes = (notes_payload.notes or "").strip()
    db.commit()
    db.refresh(center)

    return center

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Read the file content
    contents = await file.read()
    
    # Convert bytes to string
    csv_string = contents.decode('utf-8')
    
    # Use pandas to read CSV with proper handling of commas in fields
    from io import StringIO
    df = pd.read_csv(StringIO(csv_string))
    
    # Process each row
    for _, row in df.iterrows():
        # Extract city using Gemini API
        city = get_city_from_gemini(row["Address"])
        notes_value = row.get("Notes", "")
        if pd.isna(notes_value):
            notes_value = ""
        
        center = CTScanCenter(
            center_name=row["Center Name"],
            address=row["Address"],
            contact_details=row["Contact Details"],
            google_maps_link=row["Google Maps Link"],
            city=city,
            validated=False,  # Default to False for new records
            qualified=False,  # Default to False for new records
            notes=str(notes_value)
        )
        db.add(center)
    
    db.commit()
    return {"message": "File uploaded and data added successfully"}

@app.put("/api/centers/{center_id}/validate")
def update_center_validation(center_id: int, validated: bool = Query(...), db: Session = Depends(get_db)):
    """Update validation status for a specific center"""
    center = db.query(CTScanCenter).filter(CTScanCenter.id == center_id).first()
    
    if not center:
        return {"error": "Center not found"}
    
    center.validated = validated
    db.commit()
    
    return {"message": f"Center {center_id} validation status updated to {validated}"}


@app.put("/api/centers/{center_id}/qualify")
def update_center_qualification(center_id: int, qualified: bool = Query(...), db: Session = Depends(get_db)):
    """Update qualification status for a specific center"""
    center = db.query(CTScanCenter).filter(CTScanCenter.id == center_id).first()
    
    if not center:
        return {"error": "Center not found"}
    
    center.qualified = qualified
    db.commit()
    
    return {"message": f"Center {center_id} qualification status updated to {qualified}"}


@app.post("/api/update-cities")
def update_all_cities(db: Session = Depends(get_db)):
    """Update all existing records with cities extracted from their addresses using Gemini API"""
    all_centers = db.query(CTScanCenter).all()
    
    updated_count = 0
    for center in all_centers:
        # Extract city using Gemini API
        new_city = get_city_from_gemini(center.address)
        
        # Always update the city field (even if it's the same)
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
    
    # Get validated and qualified counts
    validated_centers = db.query(CTScanCenter).filter(CTScanCenter.validated == True).count()
    qualified_centers = db.query(CTScanCenter).filter(CTScanCenter.qualified == True).count()
    
    return {
        "total_centers": total_centers,
        "cities_count": len(city_counts),
        "validated_cities": validated_cities,
        "validated_centers": validated_centers,
        "qualified_centers": qualified_centers,
        "city_distribution": [{"city": row[0], "count": row[1]} for row in city_counts]
    }


@app.delete("/api/deduplicate")
def remove_duplicates(db: Session = Depends(get_db)):
    """Remove duplicate records using normalized addresses and names"""
    # Get all centers ordered by id
    all_centers = db.query(CTScanCenter).order_by(CTScanCenter.id).all()
    
    # Track seen entries by normalized address (per city) and by name if address missing
    seen_by_city: Dict[str, List[Dict[str, Any]]] = {}
    seen_by_raw_address: Dict[Tuple[str, str], int] = {}
    seen_by_name: Set[Tuple[str, str]] = set()
    duplicates_to_remove = []
    
    for center in all_centers:
        city_key = (center.city or "").strip().lower()
        address_key = normalize_address_for_dedup(center.address)
        name_key = normalize_center_name_for_dedup(center.center_name)

        if address_key:
            tokens = set(address_key.split())
            clusters = seen_by_city.setdefault(city_key, [])
            duplicate_found = False

            for cluster in clusters:
                cluster_tokens: Set[str] = cluster["tokens"]
                if not cluster_tokens and not tokens:
                    continue

                subset_match = bool(tokens) and bool(cluster_tokens) and (
                    tokens.issubset(cluster_tokens) or cluster_tokens.issubset(tokens)
                )
                if not subset_match:
                    continue

                cluster_names: Set[str] = cluster["names"]
                if name_key:
                    name_overlap = name_key in cluster_names or "" in cluster_names
                else:
                    name_overlap = True

                if not name_overlap:
                    continue

                # Choose which record to retain based on address detail
                if cluster_tokens.issubset(tokens) and tokens != cluster_tokens:
                    # New entry is more detailed – replace the kept record
                    duplicates_to_remove.append(cluster["id"])
                    cluster["id"] = center.id
                    cluster["tokens"] = tokens
                    cluster["names"] = {name_key or ""}
                else:
                    duplicates_to_remove.append(center.id)
                    cluster_names.add(name_key or "")

                duplicate_found = True
                break

            if duplicate_found:
                continue

            clusters.append(
                {
                    "id": center.id,
                    "tokens": tokens,
                    "names": {name_key or ""},
                }
            )
            continue

        if name_key:
            # Fallback when address is empty/unusable: dedupe by normalized name per city
            name_only_key = (city_key, name_key)
            if name_only_key in seen_by_name:
                duplicates_to_remove.append(center.id)
                continue
            seen_by_name.add(name_only_key)
            continue

        # If both address and name are missing, we cannot deduplicate reliably – keep the record
        if not center.address and not center.center_name:
            continue
        # Last resort: use raw lowercase address string
        raw_address = (center.address or "").strip().lower()
        if not raw_address:
            continue
        fallback_key = (city_key, raw_address)
        if fallback_key in seen_by_raw_address:
            duplicates_to_remove.append(center.id)
        else:
            seen_by_raw_address[fallback_key] = center.id
    
    # Remove the duplicates from the database
    if duplicates_to_remove:
        db.query(CTScanCenter).filter(CTScanCenter.id.in_(duplicates_to_remove)).delete()
        db.commit()
        
    return {
        "message": f"Removed {len(duplicates_to_remove)} duplicate records",
        "duplicates_removed": len(duplicates_to_remove)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)
