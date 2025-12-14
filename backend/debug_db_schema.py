from sqlalchemy import create_engine, inspect
# Point to the likely active DB in backend folder
engine = create_engine("sqlite:///backend/arela.db")

inspector = inspect(engine)
columns = inspector.get_columns('leads')
print("Columns in 'leads' table:")
for col in columns:
    print(f"- {col['name']} ({col['type']})")
