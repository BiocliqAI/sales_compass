
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import CTScanCenter

def fix_up_state_name():
    """
    Updates all occurrences of 'U P' in the stored_state column
    to 'Uttar Pradesh'.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "backend", "ct_scan_centers.db")
    DATABASE_URL = f"sqlite:///{db_path}"
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Find all centers with the state 'U P'
        centers_to_update = db.query(CTScanCenter).filter(
            CTScanCenter.stored_state == "U P"
        ).all()
        
        if not centers_to_update:
            print("No centers found with the state 'U P'. No changes needed.")
            return
            
        print(f"Found {len(centers_to_update)} center(s) with state 'U P'. Updating them to 'Uttar Pradesh'...")
        
        # Update the state for each center
        for center in centers_to_update:
            center.stored_state = "Uttar Pradesh"
            
        db.commit()
        print("Update complete. All records have been updated.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_up_state_name()
