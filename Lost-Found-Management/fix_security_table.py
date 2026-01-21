import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'database': 'lost_found_db',
    'user': 'postgres',
    'password': 'postgres123',  # Update with your password
    'port': 5432
}

def check_current_state():
    """Check the current state of the security_question table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("Checking current table structure...\n")
    
    # Check columns
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'security_question'
        ORDER BY ordinal_position
    """)
    
    print("Current columns:")
    for col in cursor.fetchall():
        print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
    
    # Check constraints
    cursor.execute("""
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = 'security_question'
    """)
    
    print("\nCurrent constraints:")
    for constraint in cursor.fetchall():
        print(f"  - {constraint[0]}: {constraint[1]}")
    
    # Check for invalid data
    cursor.execute("""
        SELECT COUNT(*) FROM security_question WHERE claim_id = 0
    """)
    invalid_count = cursor.fetchone()[0]
    print(f"\nRecords with claim_id = 0: {invalid_count}")
    
    cursor.close()
    conn.close()

def migrate_security_question_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("\nStarting migration of security_question table...\n")
    
    try:
        # Step 1: Drop the foreign key constraint on claim_id if it exists
        print("1. Dropping foreign key constraint on claim_id...")
        cursor.execute('''
            ALTER TABLE security_question 
            DROP CONSTRAINT IF EXISTS security_question_claim_id_fkey
        ''')
        conn.commit()
        print("   ✓ Done")
        
        # Step 2: Make claim_id nullable
        print("2. Making claim_id nullable...")
        cursor.execute('''
            ALTER TABLE security_question 
            ALTER COLUMN claim_id DROP NOT NULL
        ''')
        conn.commit()
        print("   ✓ Done")
        
        # Step 3: Add item_id column if it doesn't exist
        print("3. Checking item_id column...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'security_question' AND column_name = 'item_id'
        """)
        if cursor.fetchone():
            print("   ✓ item_id column already exists")
        else:
            print("   Adding item_id column...")
            cursor.execute('''
                ALTER TABLE security_question 
                ADD COLUMN item_id INTEGER
            ''')
            conn.commit()
            print("   ✓ Done")
        
        # Step 4: Add foreign key constraint to item_id if it doesn't exist
        print("4. Adding foreign key constraint to item_id...")
        cursor.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'security_question' 
            AND constraint_name = 'security_question_item_id_fkey'
        """)
        if cursor.fetchone():
            print("   ✓ Foreign key constraint already exists")
        else:
            cursor.execute('''
                ALTER TABLE security_question 
                ADD CONSTRAINT security_question_item_id_fkey 
                FOREIGN KEY (item_id) REFERENCES item(item_id) ON DELETE CASCADE
            ''')
            conn.commit()
            print("   ✓ Done")
        
        # Step 5: Clean up any invalid data (claim_id = 0)
        print("5. Cleaning up invalid data...")
        cursor.execute('''
            SELECT COUNT(*) FROM security_question WHERE claim_id = 0
        ''')
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"   Found {count} records with claim_id = 0")
            cursor.execute('''
                UPDATE security_question 
                SET claim_id = NULL 
                WHERE claim_id = 0
            ''')
            conn.commit()
            print(f"   ✓ Updated {count} records")
        else:
            print("   ✓ No invalid data found")
        
        # Step 6: Re-add foreign key constraint to claim_id (nullable)
        print("6. Re-adding foreign key constraint to claim_id...")
        cursor.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'security_question' 
            AND constraint_name = 'security_question_claim_id_fkey'
        """)
        if cursor.fetchone():
            print("   ✓ Foreign key constraint already exists")
        else:
            cursor.execute('''
                ALTER TABLE security_question 
                ADD CONSTRAINT security_question_claim_id_fkey 
                FOREIGN KEY (claim_id) REFERENCES claim_request(claim_id) ON DELETE CASCADE
            ''')
            conn.commit()
            print("   ✓ Done")
        
        print("\n" + "="*60)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nTable structure updated:")
        print("  - claim_id: nullable, with foreign key to claim_request")
        print("  - item_id: with foreign key to item")
        print("\nUsage:")
        print("  - Reporter's security questions: claim_id = NULL, item_id = <item_id>")
        print("  - Claimant's security answers: claim_id = <claim_id>, item_id = <item_id>")
        print("\nYou can now run your application without errors!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure no claims are currently being processed")
        print("2. Check if there are any orphaned records in security_question")
        print("3. You may need to manually delete invalid records first")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    check_current_state()
    print("\n" + "="*60)
    migrate_security_question_table()