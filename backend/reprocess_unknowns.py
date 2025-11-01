
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import CTScanCenter, _load_env_from_file
from city_utils import get_city_and_state_from_address

def reprocess_unknown_states():
    """
    Finds all centers with 'Unknown State', re-runs address extraction,
    and updates them in the database.
    """
    _load_env_from_file()
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "backend", "ct_scan_centers.db")
    DATABASE_URL = f"sqlite:///{db_path}"
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        unknown_state_centers = db.query(CTScanCenter).filter(CTScanCenter.stored_state == "Unknown State").all()
        
        if not unknown_state_centers:
            print("No centers with 'Unknown State' found.")
            return
            
        print(f"Found {len(unknown_state_centers)} centers with 'Unknown State'. Reprocessing...")
        print("-" * 60)
        
        for center in unknown_state_centers:
            address = center.address
            print(f"Processing ID {center.id}: {address}")
            
            if not address or not address.strip():
                print("  -> Address is empty. Cannot process.")
                continue

            new_city, new_state = get_city_and_state_from_address(address)
            
            print(f"  -> Old: City='{center.city}', State='{center.stored_state}'")
            print(f"  -> New: City='{new_city}', State='{new_state}'")
            
            if new_state != "Unknown State":
                center.city = new_city
                center.stored_state = new_state
                print("  -> UPDATE: Database record will be updated.")
            else:
                print("  -> NO CHANGE: API still returned Unknown State.")
            
            print("-" * 60)

        db.commit()
        print("Reprocessing complete. All changes have been saved to the database.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reprocess_unknown_states()
