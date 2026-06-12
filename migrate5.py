from app.database import engine
from sqlalchemy import text

def add_columns():
    with engine.begin() as conn:
        try:
            # Add columns
            conn.execute(text("ALTER TABLE camera_rent ADD paid_amount DECIMAL(12, 2);"))
            conn.execute(text("ALTER TABLE camera_rent ADD pending_amount DECIMAL(12, 2);"))
            
            # Set default values for existing rows
            conn.execute(text("""
                UPDATE camera_rent
                SET 
                    paid_amount = CASE WHEN work_status = 'Done' THEN total_amount ELSE 0.0 END,
                    pending_amount = CASE WHEN work_status = 'Pending' THEN total_amount ELSE 0.0 END
            """))
            
            # Make columns non-nullable
            conn.execute(text("ALTER TABLE camera_rent ALTER COLUMN paid_amount DECIMAL(12, 2) NOT NULL;"))
            conn.execute(text("ALTER TABLE camera_rent ALTER COLUMN pending_amount DECIMAL(12, 2) NOT NULL;"))
            
            print("Successfully added paid_amount and pending_amount columns to camera_rent.")
        except Exception as e:
            print(f"Error adding columns: {e}")

if __name__ == "__main__":
    add_columns()
