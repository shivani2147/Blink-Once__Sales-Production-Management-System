from app.database import engine
from sqlalchemy import text

def add_columns():
    with engine.begin() as conn:
        try:
            # Add columns
            conn.execute(text("ALTER TABLE clients_editing ADD paid_amount FLOAT;"))
            conn.execute(text("ALTER TABLE clients_editing ADD pending_amount FLOAT;"))
            
            # Set default values for existing rows
            # We'll assume if work is done, it's fully paid. Otherwise 0.
            conn.execute(text("""
                UPDATE clients_editing
                SET 
                    paid_amount = CASE WHEN work_status = 'Done' THEN total_amount ELSE 0.0 END,
                    pending_amount = CASE WHEN work_status = 'Pending' THEN total_amount ELSE 0.0 END
            """))
            
            # Make columns non-nullable
            conn.execute(text("ALTER TABLE clients_editing ALTER COLUMN paid_amount FLOAT NOT NULL;"))
            conn.execute(text("ALTER TABLE clients_editing ALTER COLUMN pending_amount FLOAT NOT NULL;"))
            
            print("Successfully added paid_amount and pending_amount columns to clients_editing.")
        except Exception as e:
            print(f"Error adding columns: {e}")

if __name__ == "__main__":
    add_columns()
