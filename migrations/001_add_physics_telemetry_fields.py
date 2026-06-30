import os
import sys
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Migration.001")

def get_db_path():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(project_root, "rrm_database.db")

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def run_migration():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        logger.warning(f"Database not found at {db_path}. Assuming fresh start.")
        return

    logger.info(f"Running Migration 001 on database: {db_path}")

    # New columns to add to telemetry table
    new_columns = [
        ("path_loss_db", "REAL"),
        ("estimated_rx_power_dbm", "REAL"),
        ("sinr_db", "REAL"),
        ("mcs_index", "REAL"),
        ("phy_rate_mbps", "REAL"),
        ("latency_ms", "REAL"),
        ("throughput_mbps", "REAL")
    ]

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='telemetry'")
            if not cursor.fetchone():
                logger.warning("Table 'telemetry' does not exist yet. Schema will be created by SQLAlchemy.")
                return

            # Add missing columns
            for col_name, col_type in new_columns:
                if not column_exists(cursor, "telemetry", col_name):
                    logger.info(f"Adding column '{col_name}' ({col_type}) to 'telemetry' table...")
                    cursor.execute(f"ALTER TABLE telemetry ADD COLUMN {col_name} {col_type}")
                else:
                    logger.info(f"Column '{col_name}' already exists in 'telemetry' table. Skipping.")
            
            conn.commit()
            logger.info("Migration 001 completed successfully.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
