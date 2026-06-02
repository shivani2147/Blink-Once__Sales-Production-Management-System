from app.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
print('tables:', inspector.get_table_names())
if 'post_production' in inspector.get_table_names():
    cols = inspector.get_columns('post_production')
    for c in cols:
        print(c['name'], c['type'], c['nullable'], c.get('default'))
else:
    print('post_production table not found')
