from app.database import engine
from sqlalchemy import text

def add_columns():
    with engine.begin() as conn:
        try:
            # Add columns
            conn.execute(text("ALTER TABLE monthly_financial_reports ADD project_name VARCHAR(255);"))
            
            print("Successfully added project_name column to monthly_financial_reports.")
        except Exception as e:
            print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_columns()
