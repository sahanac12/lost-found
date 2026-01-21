import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'database': 'lost_found_db',
    'user': 'postgres',
    'password': 'postgres123',  # Update with your password
    'port': 5432
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

print("Updating security_question table...")

try:
    # Add item_id column to security_question table
    cursor.execute('''
        ALTER TABLE security_question 
        ADD COLUMN IF NOT EXISTS item_id INTEGER REFERENCES item(item_id) ON DELETE CASCADE
    ''')
    
    # Make claim_id nullable since reporter's security questions don't have a claim yet
    cursor.execute('''
        ALTER TABLE security_question 
        ALTER COLUMN claim_id DROP NOT NULL
    ''')
    
    conn.commit()
    print("✓ Security_question table updated successfully!")
    print("  - Added item_id column")
    print("  - Made claim_id nullable")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")

cursor.close()
conn.close()