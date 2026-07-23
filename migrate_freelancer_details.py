import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

def migrate():
    print("Starting migration...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE monthly_financial_reports ADD freelancer_details NVARCHAR(MAX) NULL;"))
            print("Added 'freelancer_details' column successfully.")
        except Exception as e:
            print(f"Could not add 'freelancer_details' (may already exist): {e}")
        conn.commit()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
