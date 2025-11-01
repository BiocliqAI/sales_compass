
import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import CTScanCenter, Base, _load_env_from_file
from city_utils import get_city_and_state_from_address

def repopulate_database():
    """
    Clears the ct_scan_centers table and repopulates it from CSV files,
    extracting city and state for each address.
    """
    _load_env_from_file()
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "ct_scan_centers.db")
    DATABASE_URL = f"sqlite:///{db_path}"
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        print("Clearing existing data from the 'ct_scan_centers' table...")
        db.query(CTScanCenter).delete()
        db.commit()
        print("Table cleared.")

        # Find and process CSV files
        csv_files = [f for f in os.listdir(project_root) if f.endswith(".csv") and f.startswith("CT_Scan_Results")]
        if not csv_files:
            print("No CT Scan result CSV files found.")
            return

        print(f"Found {len(csv_files)} CSV files. Starting data population...")
        
        total_rows = 0
        for file_name in csv_files:
            print(f"Processing {file_name}...")
            file_path = os.path.join(project_root, file_name)
            df = pd.read_csv(file_path)
            
            for index, row in df.iterrows():
                address = row.get("Address")
                if not address or not str(address).strip():
                    print(f"  - Skipping row {index + 1} (empty address).")
                    continue

                city, state = get_city_and_state_from_address(address)
                
                center = CTScanCenter(
                    center_name=row.get("Center Name"),
                    address=address,
                    contact_details=row.get("Contact Details"),
                    google_maps_link=row.get("Google Maps Link"),
                    city=city,
                    stored_state=state,
                    notes=str(row.get("Notes", "") or "")
                )
                db.add(center)
                total_rows += 1

            db.commit()
            print(f"Finished processing {file_name}.")

        print("-" * 50)
        print(f"Database repopulation complete. Added {total_rows} new records.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    repopulate_database()
