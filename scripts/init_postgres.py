"""Initialize PostgreSQL schema for AMHI Production MVP.

This script connects to the PostgreSQL database defined in DATABASE_URL
and automatically runs all migrations in src/infrastructure/persistence/migrations/.
"""

import os
import sys
from pathlib import Path

# Ensure src/ is in PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from infrastructure.persistence.postgres_repository import connect_postgres

def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set.")
        sys.exit(1)
    
    print(f"Connecting to database to apply migrations...")
    try:
        # connect_postgres automatically calls _apply_migrations
        conn = connect_postgres(database_url)
        conn.close()
        print("PostgreSQL migrations applied successfully.")
    except Exception as e:
        print(f"Failed to initialize PostgreSQL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
