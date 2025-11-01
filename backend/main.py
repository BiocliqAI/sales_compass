import os
import pandas as pd
from fastapi import FastAPI, File, UploadFile, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List
from io import StringIO

from city_utils import get_city_and_state_from_address


def _load_env_from_file() -> None:
    """Populate environment variables from a local .env file if present."""
    if os.getenv("GEMINI_API_KEY"):
        return
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as env_file:
                for line in env_file:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or "=" not in stripped:
                        continue
                    key, value = stripped.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))
        except OSError as exc:
            print(f"Warning: could not read .env file ({exc}).")

_load_env_from_file()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ct_scan_centers.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)


class CTScanCenter(Base):
    __tablename__ = "ct_scan_centers"
    id = Column(Integer, primary_key=True, index=True)
    center_name = Column(String, index=True)
    address = Column(String)
    contact_details = Column(String)
    google_maps_link = Column(String)
    city = Column(String, index=True)
    validated = Column(Boolean, default=False)
    qualified = Column(Boolean, default=False)
    existing_client = Column(Boolean, default=False)
    not_to_pursue = Column(Boolean, default=False)
    notes = Column(Text, default="")
    stored_state = Column(String, default=None)

    @property
    def state(self) -> str:
        return self.stored_state or "Unknown State"

Base.metadata.create_all(bind=engine)

def ensure_database_columns():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(ct_scan_centers)"))
        columns = {row[1] for row in result}
        if "notes" not in columns:
            conn.execute(text("ALTER TABLE ct_scan_centers ADD COLUMN notes TEXT DEFAULT ''"))
        if "stored_state" not in columns:
            conn.execute(text("ALTER TABLE ct_scan_centers ADD COLUMN stored_state TEXT DEFAULT NULL"))
        if "existing_client" not in columns:
            conn.execute(text("ALTER TABLE ct_scan_centers ADD COLUMN existing_client BOOLEAN DEFAULT FALSE"))
        if "not_to_pursue" not in columns:
            conn.execute(text("ALTER TABLE ct_scan_centers ADD COLUMN not_to_pursue BOOLEAN DEFAULT FALSE"))
        conn.commit()

ensure_database_columns()

class CTScanCenterSchema(BaseModel):
    id: int
    center_name: str | None
    address: str | None
    contact_details: str | None
    google_maps_link: str | None
    city: str | None
    state: str | None
    validated: bool
    qualified: bool
    existing_client: bool
    not_to_pursue: bool
    notes: str | None

    class Config:
        from_attributes = True

class CTScanCenterUpdateSchema(BaseModel):
    center_name: str
    address: str
    contact_details: str
    google_maps_link: str
    city: str
    validated: bool
    qualified: bool
    existing_client: bool
    not_to_pursue: bool
    notes: str | None = ""

class StatusUpdateSchema(BaseModel):
    validated: bool
    qualified: bool
    existing_client: bool
    not_to_pursue: bool

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                city, state = get_city_and_state_from_address(row["Address"])
                center = CTScanCenter(
                    center_name=row["Center Name"],
                    address=row["Address"],
                    contact_details=row["Contact Details"],
                    google_maps_link=row["Google Maps Link"],
                    city=city,
                    stored_state=state,
                    notes=str(row.get("Notes", "") or "")
                )
                db.add(center)
        db.commit()
    db.close()

@app.get("/api/centers", response_model=List[CTScanCenterSchema])
def get_centers(db: Session = Depends(get_db)):
    return db.query(CTScanCenter).all()

@app.put("/api/centers/{center_id}", response_model=CTScanCenterSchema)
def update_center(center_id: int, center_data: CTScanCenterUpdateSchema, db: Session = Depends(get_db)):
    center = db.query(CTScanCenter).filter(CTScanCenter.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")
    
    # When the address is updated, re-fetch city and state
    if center.address != center_data.address.strip():
        new_city, new_state = get_city_and_state_from_address(center_data.address)
        center.city = new_city
        center.stored_state = new_state
    else:
        center.city = center_data.city.strip()

    center.center_name = center_data.center_name.strip()
    center.address = center_data.address.strip()
    center.contact_details = center_data.contact_details.strip()
    center.google_maps_link = center_data.google_maps_link.strip()
    center.validated = center_data.validated
    center.qualified = center_data.qualified
    center.existing_client = center_data.existing_client
    center.not_to_pursue = center_data.not_to_pursue
    center.notes = (center_data.notes or "").strip()
    
    db.commit()
    db.refresh(center)
    return center

@app.put("/api/centers/{center_id}/status", response_model=CTScanCenterSchema)
def update_status(center_id: int, status_data: StatusUpdateSchema, db: Session = Depends(get_db)):
    center = db.query(CTScanCenter).filter(CTScanCenter.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")

    center.validated = status_data.validated
    center.qualified = status_data.qualified
    center.existing_client = status_data.existing_client
    center.not_to_pursue = status_data.not_to_pursue
    
    db.commit()
    db.refresh(center)
    return center

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Check if the file has been uploaded before
    existing_file = db.query(UploadedFile).filter(UploadedFile.filename == file.filename).first()
    if existing_file:
        raise HTTPException(status_code=409, detail=f"File '{file.filename}' has already been uploaded.")

    contents = await file.read()
    df = pd.read_csv(StringIO(contents.decode('utf-8')))
    for _, row in df.iterrows():
        city, state = get_city_and_state_from_address(row["Address"])
        center = CTScanCenter(
            center_name=row["Center Name"],
            address=row["Address"],
            contact_details=row["Contact Details"],
            google_maps_link=row["Google Maps Link"],
            city=city,
            stored_state=state,
            notes=str(row.get("Notes", "") or "")
        )
        db.add(center)
    
    # Add the filename to the tracking table
    new_uploaded_file = UploadedFile(filename=file.filename)
    db.add(new_uploaded_file)
    
    db.commit()
    return {"message": "File uploaded and data added successfully"}

@app.post("/api/refresh-all-data")
def refresh_all_data(db: Session = Depends(get_db)):
    all_centers = db.query(CTScanCenter).all()
    updated_count = 0
    for center in all_centers:
        new_city, new_state = get_city_and_state_from_address(center.address)
        if new_city != center.city or new_state != center.stored_state:
            center.city = new_city
            center.stored_state = new_state
            updated_count += 1
    db.commit()
    return {
        "message": f"Refreshed {updated_count} of {len(all_centers)} records.",
        "total_processed": len(all_centers),
        "updated_count": updated_count,
    }

@app.get("/api/states")
def get_states(db: Session = Depends(get_db)):
    states = db.query(CTScanCenter.stored_state).distinct().all()
    return sorted([state[0] for state in states if state[0] and state[0] != "Unknown State"])

@app.get("/api/centers-by-state/{state_name}", response_model=List[CTScanCenterSchema])
def get_centers_by_state(state_name: str, db: Session = Depends(get_db)):
    return db.query(CTScanCenter).filter(CTScanCenter.stored_state == state_name).all()

@app.delete("/api/centers/{center_id}", status_code=204)
def delete_center(center_id: int, db: Session = Depends(get_db)):
    center = db.query(CTScanCenter).filter(CTScanCenter.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")
    db.delete(center)
    db.commit()
    return


@app.delete("/api/deduplicate", status_code=200)
def remove_duplicates(db: Session = Depends(get_db)):
    """
    Finds and removes duplicate records based on the address.
    Keeps the first record found and deletes subsequent duplicates.
    """
    from sqlalchemy import func

    # Find addresses that have duplicates
    duplicate_addresses = (
        db.query(CTScanCenter.address, func.count(CTScanCenter.id).label("count"))
        .group_by(CTScanCenter.address)
        .having(func.count(CTScanCenter.id) > 1)
        .all()
    )

    duplicates_removed = 0
    for address, count in duplicate_addresses:
        # Get all IDs for this address, ordered by ID
        ids_to_check = (
            db.query(CTScanCenter.id)
            .filter(CTScanCenter.address == address)
            .order_by(CTScanCenter.id)
            .all()
        )
        
        # Keep the first one, delete the rest
        ids_to_delete = [id_tuple[0] for id_tuple in ids_to_check[1:]]
        
        if ids_to_delete:
            db.query(CTScanCenter).filter(CTScanCenter.id.in_(ids_to_delete)).delete(synchronize_session=False)
            duplicates_removed += len(ids_to_delete)

    db.commit()
    return {"duplicates_removed": duplicates_removed}


class PotentialDuplicatePair(BaseModel):
    center1: CTScanCenterSchema
    center2: CTScanCenterSchema
    similarity_score: int

class MergeRequest(BaseModel):
    id_to_keep: int
    id_to_delete: int


@app.get("/api/potential-duplicates", response_model=List[PotentialDuplicatePair])
def find_potential_duplicates(db: Session = Depends(get_db)):
    from thefuzz import fuzz
    import re
    import logging

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

    try:
        log.info("Starting potential duplicate analysis...")

        def normalize_text(text: str | None) -> str:
            if not text:
                return ""
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        all_centers = db.query(CTScanCenter).all()
        log.info(f"Loaded {len(all_centers)} centers from the database.")
        
        potential_duplicates = []
        checked_pairs = set()
        
        total_comparisons = len(all_centers) * (len(all_centers) - 1) // 2
        log.info(f"Performing approximately {total_comparisons} comparisons...")

        for i in range(len(all_centers)):
            for j in range(i + 1, len(all_centers)):
                if (i % 100 == 0 and j == i + 1):
                    log.info(f"Processing outer loop index {i}...")

                center1 = all_centers[i]
                center2 = all_centers[j]

                pair_key = tuple(sorted((center1.id, center2.id)))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                name1 = normalize_text(center1.center_name)
                name2 = normalize_text(center2.center_name)
                address1 = normalize_text(center1.address)
                address2 = normalize_text(center2.address)

                name_similarity = fuzz.token_set_ratio(name1, name2)
                address_similarity = fuzz.token_set_ratio(address1, address2)
                
                final_score = int((name_similarity * 0.4) + (address_similarity * 0.6))

                if final_score > 85:
                    log.info(f"Found potential duplicate pair with score {final_score}: ID {center1.id} and ID {center2.id}")
                    potential_duplicates.append(
                        PotentialDuplicatePair(
                            center1=center1,
                            center2=center2,
                            similarity_score=final_score
                        )
                    )
        
        log.info("Analysis complete. Sorting results.")
        sorted_duplicates = sorted(potential_duplicates, key=lambda x: x.similarity_score, reverse=True)
        log.info(f"Returning {len(sorted_duplicates)} potential duplicate pairs.")
        return sorted_duplicates
    except Exception as e:
        log.error(f"An error occurred during duplicate analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")


@app.post("/api/merge-duplicates", response_model=CTScanCenterSchema)
def merge_duplicates(merge_request: MergeRequest, db: Session = Depends(get_db)):
    center_to_keep = db.query(CTScanCenter).filter(CTScanCenter.id == merge_request.id_to_keep).first()
    center_to_delete = db.query(CTScanCenter).filter(CTScanCenter.id == merge_request.id_to_delete).first()

    if not center_to_keep or not center_to_delete:
        raise HTTPException(status_code=404, detail="One or both centers not found")

    # Smart merge logic
    if not center_to_keep.contact_details and center_to_delete.contact_details:
        center_to_keep.contact_details = center_to_delete.contact_details
    if not center_to_keep.google_maps_link and center_to_delete.google_maps_link:
        center_to_keep.google_maps_link = center_to_delete.google_maps_link
    if center_to_delete.notes:
        center_to_keep.notes = (center_to_keep.notes or "") + " | Merged from deleted record: " + center_to_delete.notes

    db.delete(center_to_delete)
    db.commit()
    db.refresh(center_to_keep)
    
    return center_to_keep


@app.post("/api/auto-merge-duplicates", status_code=200)
def auto_merge_duplicates(db: Session = Depends(get_db)):
    from thefuzz import fuzz
    import re
    import logging

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

    log.info("Starting automatic duplicate merging process...")

    def normalize_text(text: str | None) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    all_centers = db.query(CTScanCenter).order_by(CTScanCenter.id).all()
    center_map = {c.id: c for c in all_centers}
    deleted_ids = set()
    merged_count = 0

    log.info(f"Loaded {len(all_centers)} centers for auto-merging.")

    for i in range(len(all_centers)):
        center1 = all_centers[i]
        if center1.id in deleted_ids:
            continue

        for j in range(i + 1, len(all_centers)):
            center2 = all_centers[j]
            if center2.id in deleted_ids:
                continue

            name1 = normalize_text(center1.center_name)
            name2 = normalize_text(center2.center_name)
            address1 = normalize_text(center1.address)
            address2 = normalize_text(center2.address)

            name_similarity = fuzz.token_set_ratio(name1, name2)
            address_similarity = fuzz.token_set_ratio(address1, address2)
            final_score = int((name_similarity * 0.4) + (address_similarity * 0.6))

            if final_score > 85:
                # Keep the one with the lower ID (center1 is guaranteed to have a lower ID here)
                center_to_keep = center1
                center_to_delete = center2

                log.info(f"Merging ID {center_to_delete.id} into ID {center_to_keep.id} (Score: {final_score})")

                # Smart merge
                if not center_to_keep.contact_details and center_to_delete.contact_details:
                    center_to_keep.contact_details = center_to_delete.contact_details
                if not center_to_keep.google_maps_link and center_to_delete.google_maps_link:
                    center_to_keep.google_maps_link = center_to_delete.google_maps_link
                if center_to_delete.notes:
                    center_to_keep.notes = (center_to_keep.notes or "") + f" | Merged from deleted ID {center_to_delete.id}: " + center_to_delete.notes

                db.delete(center_to_delete)
                deleted_ids.add(center_to_delete.id)
                merged_count += 1
    
    db.commit()
    log.info(f"Auto-merge complete. Merged {merged_count} records.")
    return {"duplicates_merged": merged_count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)
