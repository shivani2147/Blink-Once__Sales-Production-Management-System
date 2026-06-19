"""
Add `requirements` column to three_months_client_followup table.
Run: python -m app.scripts.alter_followup_add_requirements
Backup DB before running.
"""
from sqlalchemy import text
from app.database import engine

SQL_ALTER = '''
ALTER TABLE three_months_client_followup
ADD requirements NVARCHAR(MAX) NULL;
'''

SQL_PREVIEW = '''
SELECT TOP 10 id, [date], client_name, requirements, comment
FROM three_months_client_followup
ORDER BY [date] DESC;
'''


def main():
    print("Previewing top 10 rows (before alter):")
    with engine.connect() as conn:
        rows = conn.execute(text(SQL_PREVIEW)).fetchmany(10)
        for r in rows:
            print(r)

    confirm = input("Proceed to add 'requirements' column? (yes/no): ")
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
