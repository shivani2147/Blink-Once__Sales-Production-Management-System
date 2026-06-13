import sqlalchemy
from app.database import engine

def migrate():
    with engine.connect() as conn:
        tables = ["pre_production", "on_production", "post_production"]
        
        for table in tables:
            print(f"Migrating table: {table}")
            try:
                conn.execute(sqlalchemy.text(f"ALTER TABLE {table} ADD year INT"))
                print(f"Added 'year' column to {table}.")
            except Exception as e:
                print(f"Error adding 'year' to {table}: {e}")

            try:
                conn.execute(sqlalchemy.text(f"ALTER TABLE {table} ADD month VARCHAR(20)"))
                print(f"Added 'month' column to {table}.")
            except Exception as e:
                print(f"Error adding 'month' to {table}: {e}")
                
        conn.commit()

if __name__ == "__main__":
    migrate()
