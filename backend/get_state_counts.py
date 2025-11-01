
import os
import sys
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import CTScanCenter

def get_state_counts():
    """
    Connects to the database and prints the number of centers per state.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "ct_scan_centers.db")
    DATABASE_URL = f"sqlite:///{db_path}"
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Querying database for state counts...")
        print("-" * 40)
        
        results = db.query(
            CTScanCenter.stored_state, 
            func.count(CTScanCenter.id)
        ).group_by(CTScanCenter.stored_state).all()
        
        if not results:
            print("No data found in the database.")
            return
            
        total_centers = 0
        for state, count in results:
            state_name = state if state else "Unknown State"
            print(f"- {state_name}: {count} centers")
            total_centers += count
            
        print("-" * 40)
        print(f"Total centers found: {total_centers}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    get_state_counts()
