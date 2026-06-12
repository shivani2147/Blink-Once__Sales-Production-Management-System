from app.database import engine
from sqlalchemy import text

def add_columns():
    with engine.begin() as conn:
        try:
            # Add columns
            conn.execute(text("ALTER TABLE investment_to_grow_company ADD paid_amount FLOAT;"))
            conn.execute(text("ALTER TABLE investment_to_grow_company ADD pending_amount FLOAT;"))
            
            # Set default values for existing rows
            conn.execute(text("""
                UPDATE investment_to_grow_company
                SET 
                    paid_amount = CASE WHEN payment_status = 'Done' OR payment_status IS NULL THEN total_amount ELSE 0.0 END,
                    pending_amount = CASE WHEN payment_status = 'Pending' THEN total_amount ELSE 0.0 END
            """))
            
            # Make columns non-nullable
            conn.execute(text("ALTER TABLE investment_to_grow_company ALTER COLUMN paid_amount FLOAT NOT NULL;"))
            conn.execute(text("ALTER TABLE investment_to_grow_company ALTER COLUMN pending_amount FLOAT NOT NULL;"))
            
            print("Successfully added paid_amount and pending_amount columns.")
        except Exception as e:
            print(f"Error adding columns: {e}")

if __name__ == "__main__":
    add_columns()
