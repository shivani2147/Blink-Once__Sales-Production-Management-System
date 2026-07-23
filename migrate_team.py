import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

def migrate():
    print("Starting migration...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE monthly_financial_reports ADD team NVARCHAR(255) NULL;"))
            print("Added 'team' column successfully.")
        except Exception as e:
            print(f"Error adding 'team' column (maybe it already exists?): {e}")

        try:
            conn.execute(text("ALTER TABLE monthly_financial_reports DROP COLUMN project_name;"))
            print("Dropped 'project_name' column successfully.")
        except Exception as e:
            print(f"Error dropping 'project_name' column: {e}")
            
        conn.commit()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
