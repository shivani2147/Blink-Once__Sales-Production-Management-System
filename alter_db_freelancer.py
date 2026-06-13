from app.database import engine
from sqlalchemy import text

def alter_db():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE freelancer_works ADD paid_amount FLOAT DEFAULT 0.0"))
            print("Added paid_amount")
        except Exception as e:
            print("paid_amount might already exist:", e)
        
        try:
            conn.execute(text("ALTER TABLE freelancer_works ADD pending_amount FLOAT DEFAULT 0.0"))
            print("Added pending_amount")
        except Exception as e:
            print("pending_amount might already exist:", e)
        
        conn.commit()

if __name__ == '__main__':
    alter_db()
