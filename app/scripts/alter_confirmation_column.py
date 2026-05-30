"""
Safe script to change `confirmation` column type to DECIMAL(18,2)
Run this from project root: `python -m app.scripts.alter_confirmation_column`
Make a DB backup before running.
"""
from sqlalchemy import text
from app.database import engine

SQL_ALTER = '''
ALTER TABLE three_months_client_followup
ALTER COLUMN confirmation DECIMAL(18,2) NOT NULL;
'''

SQL_PREVIEW = '''
SELECT id, client_name, total_amount, confirmation
FROM three_months_client_followup
ORDER BY date DESC
'''


def main():
    print("Previewing top 10 rows (before alter):")
    with engine.connect() as conn:
        rows = conn.execute(text(SQL_PREVIEW)).fetchmany(10)
        for r in rows:
            print(r)

    confirm = input("Proceed to ALTER the column to DECIMAL(18,2)? This is irreversible without a backup (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborted by user.")
        return

    try:
        with engine.begin() as conn:
            conn.execute(text(SQL_ALTER))
        print("ALTER completed successfully.")
    except Exception as e:
        print("Error during ALTER:", e)

    print("Previewing top 10 rows (after alter):")
    with engine.connect() as conn:
        rows = conn.execute(text(SQL_PREVIEW)).fetchmany(10)
        for r in rows:
            print(r)


if __name__ == '__main__':
    main()
