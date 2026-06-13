"""
Fix NULL values in freelancer_works table for paid_amount and pending_amount
"""
from app.database import engine
from sqlalchemy import text

def fix_null_values():
    with engine.connect() as conn:
        try:
            # Update paid_amount NULL values to 0.0
            conn.execute(text("UPDATE freelancer_works SET paid_amount = 0.0 WHERE paid_amount IS NULL"))
            print("✓ Updated NULL paid_amount values to 0.0")
        except Exception as e:
            print(f"⚠️  Error updating paid_amount: {e}")
        
        try:
            # Update pending_amount NULL values to total_amount
            conn.execute(text("UPDATE freelancer_works SET pending_amount = total_amount WHERE pending_amount IS NULL"))
            print("✓ Updated NULL pending_amount values to total_amount")
        except Exception as e:
            print(f"⚠️  Error updating pending_amount: {e}")
        
        try:
            # Also recalculate all pending amounts to ensure they're correct
            conn.execute(text("UPDATE freelancer_works SET pending_amount = (total_amount - paid_amount)"))
            print("✓ Recalculated all pending_amount values")
        except Exception as e:
            print(f"⚠️  Error recalculating pending_amount: {e}")
        
        conn.commit()
        print("\n✅ Database cleanup completed!")

if __name__ == '__main__':
    fix_null_values()
