
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import CTScanCenter

def update_sambhajinagar_state():
    """
    Updates the state to 'Maharashtra' for all centers located in
    'Chhatrapati Sambhajinagar' that currently have an unknown state.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "backend", "ct_scan_centers.db")
    DATABASE_URL = f"sqlite:///{db_path}"
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Find the centers to update
        centers_to_update = db.query(CTScanCenter).filter(
            CTScanCenter.city == "Chhatrapati Sambhajinagar",
            CTScanCenter.stored_state == "Unknown State"
        ).all()
        
        if not centers_to_update:
            print("No centers found in 'Chhatrapati Sambhajinagar' with an unknown state.")
            return
            
        print(f"Found {len(centers_to_update)} center(s) in 'Chhatrapati Sambhajinagar' to update.")
        
        # Update the state for each center
        for center in centers_to_update:
            print(f"Updating ID {center.id}: Setting state to 'Maharashtra'")
            center.stored_state = "Maharashtra"
            
        db.commit()
        print("Update complete. Changes have been saved.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_sambhajinagar_state()
