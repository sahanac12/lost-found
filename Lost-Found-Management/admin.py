import psycopg2
import psycopg2.extras
from werkzeug.security import check_password_hash

DB_CONFIG = {
    'host': 'localhost',
    'database': 'lost_found_db',
    'user': 'postgres',
    'password': 'postgres123',  # Update with your password
    'port': 5432
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Check admin accounts
cursor.execute('SELECT * FROM "user" WHERE role = %s', ('admin',))
admins = cursor.fetchall()

print("=" * 60)
print("ADMIN ACCOUNTS IN DATABASE")
print("=" * 60)

if admins:
    for admin in admins:
        print(f"User ID: {admin['user_id']}")
        print(f"Name: {admin['name']}")
        print(f"Email: {admin['email']}")
        print(f"Role: {admin['role']}")
        print(f"Password Hash: {admin['password_hash'][:50]}...")
        
        # Test password
        test_password = 'admin123'
        is_valid = check_password_hash(admin['password_hash'], test_password)
        print(f"Password 'admin123' valid: {is_valid}")
        print("-" * 60)
else:
    print(" No admin accounts found!")
    print("\nCreating admin account now...")
    from werkzeug.security import generate_password_hash
    
    password_hash = generate_password_hash('admin123')
    cursor.execute(
        'INSERT INTO "user" (name, email, password_hash, role) VALUES (%s, %s, %s, %s)',
        ('Admin', 'admin@admin.com', password_hash, 'admin')
    )
    conn.commit()
    print("✓ Admin account created!")
    print("Email: admin@admin.com")
    print("Password: admin123")

cursor.close()
conn.close()

print("\n" + "=" * 60)
print("To login as admin, use:")
print("Email: admin@admin.com")
print("Password: admin123")
print("=" * 60)