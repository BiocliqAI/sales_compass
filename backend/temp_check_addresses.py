
import os
import sys
import pandas as pd

# Add the backend directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import _load_env_from_file
from city_utils import get_city_and_state_from_address

def process_csv_files_sample():
    """
    Reads CSV files and processes a sample of 10 addresses to
    check the extraction function.
    """
    _load_env_from_file()
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        csv_files = [f for f in os.listdir(project_root) if f.endswith(".csv") and f.startswith("CT_Scan_Results")]
        if not csv_files:
            print("No CT Scan result CSV files found in the project root.")
            return

        print("Processing a sample of 10 addresses...")
        print("-" * 50)
        
        processed_count = 0
        for file_name in csv_files:
            if processed_count >= 10:
                break

            print(f"Reading from file: {file_name}")
            file_path = os.path.join(project_root, file_name)
            df = pd.read_csv(file_path)
            
            for index, row in df.iterrows():
                if processed_count >= 10:
                    break

                address = row.get("Address")
                if not address or not str(address).strip():
                    print(f"  Row {index + 1}: Address is empty, skipping.")
                    continue
                
                city, state = get_city_and_state_from_address(address)
                print(f"  Row {index + 1}: {address} -> City: {city}, State: {state}")
                processed_count += 1
            
            if processed_count < 10:
                print("-" * 50)

        print("-" * 50)
        print("Sample processing complete.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    process_csv_files_sample()
