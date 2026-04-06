"""
Utility script to initialize the Module C13 PostgreSQL database.
Loads src/modules/C13/projectdb.sql into the database specified in .env.
"""
import sys
from pathlib import Path

# ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.modules.C13.backend import initialize_projectdb

def main():
    print("--- MediSearch Database Initialization ---")
    try:
        result = initialize_projectdb()
        print(f"SUCCESS: {result}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
