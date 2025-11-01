
import sqlite3

def add_columns_to_db():
    conn = sqlite3.connect('ct_scan_centers.db')
    c = conn.cursor()
    
    try:
        c.execute("ALTER TABLE ct_scan_centers ADD COLUMN existing_client BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'existing_client' already exists.")
        else:
            raise
            
    try:
        c.execute("ALTER TABLE ct_scan_centers ADD COLUMN not_to_pursue BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'not_to_pursue' already exists.")
        else:
            raise

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns_to_db()
    print("Database schema updated successfully.")
