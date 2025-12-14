import sqlite3

# Connect to the database
conn = sqlite3.connect('backend/arela.db')
cursor = conn.cursor()

try:
    print("Deleting all leads...")
    cursor.execute("DELETE FROM leads")
    conn.commit()
    print(f"Deleted {cursor.rowcount} leads.")
except Exception as e:
    print(f"Error deleting leads: {e}")

conn.close()
