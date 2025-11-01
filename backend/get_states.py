
import sqlite3
import sys
import os

# Add the backend directory to the path to import city_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from city_utils import infer_state_from_city_and_address

def get_unique_states():
    """Connects to the database and prints a unique list of states."""
    db_path = os.path.join(os.path.dirname(__file__), 'ct_scan_centers.db')
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT city, address FROM ct_scan_centers")
        rows = cursor.fetchall()
        
        states = set()
        for row in rows:
            city, address = row
            state = infer_state_from_city_and_address(city, address)
            if state:
                states.add(state.strip())
        
        sorted_states = sorted(list(states))
        
        print("Found states:")
        for state in sorted_states:
            print(state)
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    get_unique_states()
