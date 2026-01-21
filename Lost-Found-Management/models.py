import sqlite3
from werkzeug.security import generate_password_hash

# You can change this to any name you want
DATABASE = 'lost_found_management.db'

def get_db_connection():
    """Create and return database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initialize database with all required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Creating database tables...")
    
    # ============================================
    # USER TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ User table created")
    
    # ============================================
    # ITEM TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Item (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'resolved', 'archived')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Item table created")
    
    # ============================================
    # REPORT TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Report (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL CHECK(report_type IN ('lost', 'found')),
            report_date TEXT NOT NULL,
            remarks TEXT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES Item(item_id) ON DELETE CASCADE
        )
    ''')
    print("✓ Report table created")
    
    # ============================================
    # CLAIM_REQUEST TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Claim_request (
            claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            proof TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES Item(item_id) ON DELETE CASCADE
        )
    ''')
    print("✓ Claim_request table created")
    
    # ============================================
    # SECURITY_QUESTION TABLE
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS security_question (
        question_id SERIAL PRIMARY KEY,
        question_text TEXT NOT NULL,
        answer TEXT NOT NULL,
        claim_id INTEGER REFERENCES claim_request(claim_id) ON DELETE CASCADE,
        item_id INTEGER NOT NULL REFERENCES item(item_id) ON DELETE CASCADE,
        CONSTRAINT check_reporter_or_claimant CHECK (
            (claim_id IS NULL AND item_id IS NOT NULL) OR 
            (claim_id IS NOT NULL AND item_id IS NOT NULL)
        )
    )
''')
    print("✓ Security_question table created")
    
    # ============================================
    # ADMIN_ACTION TABLE
    # ============================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Admin_action (
            action_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL CHECK(action_type IN ('approve', 'reject')),
            remarks TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            admin_id INTEGER NOT NULL,
            claim_id INTEGER NOT NULL,
            FOREIGN KEY (admin_id) REFERENCES User(user_id) ON DELETE CASCADE,
            FOREIGN KEY (claim_id) REFERENCES Claim_request(claim_id) ON DELETE CASCADE
        )
    ''')
    print("✓ Admin_action table created")
    
    conn.commit()
    print("\n✓ All tables created successfully!")
    
    # ============================================
    # CREATE DEFAULT ADMIN ACCOUNT
    # ============================================
    create_default_admin(conn)
    
    conn.close()

def create_default_admin(conn=None):
    """Create default admin account if it doesn't exist"""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    
    cursor = conn.cursor()
    
    # Check if admin already exists
    cursor.execute("SELECT * FROM User WHERE role = 'admin' LIMIT 1")
    admin = cursor.fetchone()
    
    if not admin:
        print("\nCreating default admin account...")
        admin_hash = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO User (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', ('System Admin', 'admin@lostfound.com', admin_hash, 'admin'))
        conn.commit()
        print("✓ Default admin created:")
        print("  Email: admin@lostfound.com")
        print("  Password: admin123")
        print("  ⚠️  IMPORTANT: Change this password after first login!")
    else:
        print("\n✓ Admin account already exists")
    
    if should_close:
        conn.close()

def drop_all_tables():
    """Drop all tables - use with caution!"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = ['Admin_action', 'Security_question', 'Claim_request', 'Report', 'Item', 'User']
    
    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS {table}')
        print(f"✓ Dropped table: {table}")
    
    conn.commit()
    conn.close()
    print("\n✓ All tables dropped successfully!")

def reset_database():
    """Reset entire database - drops and recreates all tables"""
    print("=" * 50)
    print("RESETTING DATABASE")
    print("=" * 50)
    drop_all_tables()
    print()
    init_db()
    print("=" * 50)
    print("DATABASE RESET COMPLETE")
    print("=" * 50)

# ============================================
# DATABASE HELPER FUNCTIONS
# ============================================

class User:
    """User model helper methods"""
    
    @staticmethod
    def create(name, email, password_hash, role='user'):
        """Create a new user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO User (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (name, email, password_hash, role))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    @staticmethod
    def email_exists(email):
        """Check if email already exists"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM User WHERE email = ?', (email,))
        result = cursor.fetchone()
        conn.close()
        return result['count'] > 0

class Item:
    """Item model helper methods"""
    
    @staticmethod
    def create(title, description, category, location, date):
        """Create a new item"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Item (title, description, category, location, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, category, location, date))
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return item_id
    
    @staticmethod
    def get_by_id(item_id):
        """Get item by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Item WHERE item_id = ?', (item_id,))
        item = cursor.fetchone()
        conn.close()
        return item
    
    @staticmethod
    def get_all_active():
        """Get all active items"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT i.*, r.report_type, u.name as reporter_name
            FROM Item i
            JOIN Report r ON i.item_id = r.item_id
            JOIN User u ON r.user_id = u.user_id
            WHERE i.status = 'active'
            ORDER BY i.created_at DESC
        ''')
        items = cursor.fetchall()
        conn.close()
        return items
    
    @staticmethod
    def update_status(item_id, status):
        """Update item status"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE Item SET status = ? WHERE item_id = ?', (status, item_id))
        conn.commit()
        conn.close()

class Report:
    """Report model helper methods"""
    
    @staticmethod
    def create(report_type, report_date, remarks, user_id, item_id):
        """Create a new report"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Report (report_type, report_date, remarks, user_id, item_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (report_type, report_date, remarks, user_id, item_id))
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report_id
    
    @staticmethod
    def get_by_user(user_id):
        """Get all reports by a user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, i.title, i.category, i.location, i.status
            FROM Report r
            JOIN Item i ON r.item_id = i.item_id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
        ''', (user_id,))
        reports = cursor.fetchall()
        conn.close()
        return reports
    
    @staticmethod
    def get_all():
        """Get all reports"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, i.title, i.category, i.location, i.status, u.name as reporter_name
            FROM Report r
            JOIN Item i ON r.item_id = i.item_id
            JOIN User u ON r.user_id = u.user_id
            ORDER BY r.created_at DESC
        ''')
        reports = cursor.fetchall()
        conn.close()
        return reports

class ClaimRequest:
    """Claim Request model helper methods"""
    
    @staticmethod
    def create(claim_date, proof, user_id, item_id):
        """Create a new claim request"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Claim_request (claim_date, status, proof, user_id, item_id)
            VALUES (?, 'pending', ?, ?, ?)
        ''', (claim_date, proof, user_id, item_id))
        claim_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return claim_id
    
    @staticmethod
    def get_by_user(user_id):
        """Get all claims by a user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, i.title, i.category, i.location
            FROM Claim_request c
            JOIN Item i ON c.item_id = i.item_id
            WHERE c.user_id = ?
            ORDER BY c.created_at DESC
        ''', (user_id,))
        claims = cursor.fetchall()
        conn.close()
        return claims
    
    @staticmethod
    def get_pending():
        """Get all pending claims"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, i.title, i.category, i.location, u.name as claimant_name, u.email as claimant_email
            FROM Claim_request c
            JOIN Item i ON c.item_id = i.item_id
            JOIN User u ON c.user_id = u.user_id
            WHERE c.status = 'pending'
            ORDER BY c.created_at DESC
        ''')
        claims = cursor.fetchall()
        conn.close()
        return claims
    
    @staticmethod
    def get_processed():
        """Get all processed (approved/rejected) claims"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, i.title, i.category, u.name as claimant_name, aa.action_type, aa.remarks as admin_remarks
            FROM Claim_request c
            JOIN Item i ON c.item_id = i.item_id
            JOIN User u ON c.user_id = u.user_id
            LEFT JOIN Admin_action aa ON c.claim_id = aa.claim_id
            WHERE c.status IN ('approved', 'rejected')
            ORDER BY c.created_at DESC
        ''')
        claims = cursor.fetchall()
        conn.close()
        return claims
    
    @staticmethod
    def get_by_id(claim_id):
        """Get claim details by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, i.*, u.name as claimant_name, u.email as claimant_email,
                   r.report_type, r.report_date
            FROM Claim_request c
            JOIN Item i ON c.item_id = i.item_id
            JOIN User u ON c.user_id = u.user_id
            JOIN Report r ON i.item_id = r.item_id
            WHERE c.claim_id = ?
        ''', (claim_id,))
        claim = cursor.fetchone()
        conn.close()
        return claim
    
    @staticmethod
    def update_status(claim_id, status):
        """Update claim status"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE Claim_request SET status = ? WHERE claim_id = ?', (status, claim_id))
        conn.commit()
        conn.close()

class SecurityQuestion:
    """Security Question model helper methods"""
    
    @staticmethod
    def create(question_text, answer, claim_id):
        """Create a security question"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Security_question (question_text, answer, claim_id)
            VALUES (?, ?, ?)
        ''', (question_text, answer, claim_id))
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return question_id
    
    @staticmethod
    def get_by_claim(claim_id):
        """Get security questions for a claim"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Security_question WHERE claim_id = ?', (claim_id,))
        questions = cursor.fetchall()
        conn.close()
        return questions

class AdminAction:
    """Admin Action model helper methods"""
    
    @staticmethod
    def create(action_type, remarks, admin_id, claim_id):
        """Create an admin action record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Admin_action (action_type, remarks, admin_id, claim_id)
            VALUES (?, ?, ?, ?)
        ''', (action_type, remarks, admin_id, claim_id))
        action_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return action_id
    
    @staticmethod
    def get_all():
        """Get all admin actions (audit log)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT aa.*, u.name as admin_name, c.claim_id
            FROM Admin_action aa
            JOIN User u ON aa.admin_id = u.user_id
            JOIN Claim_request c ON aa.claim_id = c.claim_id
            ORDER BY aa.timestamp DESC
        ''')
        actions = cursor.fetchall()
        conn.close()
        return actions

# ============================================
# RUN STANDALONE TO INITIALIZE DATABASE
# ============================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'reset':
            reset_database()
        elif sys.argv[1] == 'init':
            init_db()
        else:
            print("Usage: python models.py [init|reset]")
    else:
        init_db()