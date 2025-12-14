import sqlite3

# Connect to the database
conn = sqlite3.connect('backend/arela.db')
cursor = conn.cursor()

# Columns to add
columns_to_add = [
    ("zoning", "VARCHAR"),
    ("property_type", "VARCHAR"),
    ("mortgage_amount", "INTEGER"),
    ("source", "VARCHAR"),
    ("parcel_id", "VARCHAR")
]

for col_name, col_type in columns_to_add:
    try:
        print(f"Adding column {col_name}...")
        cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
        print(f"Added {col_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column {col_name} already exists.")
        else:
            print(f"Error adding {col_name}: {e}")

conn.commit()
conn.close()
print("Migration complete.")
