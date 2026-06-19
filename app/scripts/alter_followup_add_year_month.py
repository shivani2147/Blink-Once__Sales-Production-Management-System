"""
Safe script to add `year` and `month` columns to the `three_months_client_followup` table.
Run this from project root: `python -m app.scripts.alter_followup_add_year_month`
Make a DB backup before running.
"""
from sqlalchemy import text
from app.database import engine

SQL_ALTER = '''
ALTER TABLE three_months_client_followup
ADD year INT NULL,
    month VARCHAR(50) NULL;
'''

SQL_UPDATE = '''
UPDATE three_months_client_followup
SET year = YEAR([date]),
    month = DATENAME(month, [date])
WHERE year IS NULL OR month IS NULL;
'''

SQL_ALTER_NOT_NULL = '''
ALTER TABLE three_months_client_followup
ALTER COLUMN year INT NOT NULL;
ALTER TABLE three_months_client_followup
ALTER COLUMN month VARCHAR(50) NOT NULL;
'''

SQL_ADD_DEFAULTS = '''
ALTER TABLE three_months_client_followup
ADD CONSTRAINT DF_three_months_client_followup_year DEFAULT (YEAR(GETDATE())) FOR year;
ALTER TABLE three_months_client_followup
ADD CONSTRAINT DF_three_months_client_followup_month DEFAULT (DATENAME(month, GETDATE())) FOR month;
'''

SQL_PREVIEW = '''
SELECT TOP 10 id, [date], year, month, client_name, event_date, location
FROM three_months_client_followup
ORDER BY [date] DESC;
'''


def main():
    print("Previewing top 10 rows before schema change:")
    with engine.connect() as conn:
        rows = conn.execute(text(SQL_PREVIEW)).fetchmany(10)
        for r in rows:
            print(r)

    confirm = input("Proceed to add year/month columns to three_months_client_followup? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborted by user.")
        return

    try:
        with engine.begin() as conn:
            conn.execute(text(SQL_ALTER))
            conn.execute(text(SQL_UPDATE))
            conn.execute(text(SQL_ALTER_NOT_NULL))
            conn.execute(text(SQL_ADD_DEFAULTS))
        print("Schema updated successfully.")
    except Exception as e:
        print("Error during schema update:", e)
        return

    print("Previewing top 10 rows after schema change:")
    with engine.connect() as conn:
        rows = conn.execute(text(SQL_PREVIEW)).fetchmany(10)
        for r in rows:
            print(r)


if __name__ == '__main__':
    main()
