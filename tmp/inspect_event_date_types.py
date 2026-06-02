from app.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = ['pre_production', 'on_production', 'checklists', 'monthly_financial_reports', 'three_months_client_followup', 'upcoming_shoots']
for table in tables:
    if table in inspector.get_table_names():
        print('TABLE', table)
        for c in inspector.get_columns(table):
            if c['name'] == 'event_date':
                print('  event_date:', c['type'])
                break
    else:
        print('missing', table)
