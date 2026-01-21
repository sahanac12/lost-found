from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from flask_mail import Mail, Message
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta
import os
import string  # ADD THIS
import random  # ADD THIS
import time  

# Create Flask app FIRST
app = Flask(__name__)
app.secret_key = 'abd04a92802df48bf455d9eb4c6e3186325671c5fd9c59c1df56e31e8eb98088'

# Configure Mail BEFORE initializing
# Email Configuration for Mailtrap
# Email Configuration for Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'sahanac2024@gmail.com'  # Your Gmail
app.config['MAIL_PASSWORD'] = 'ovvr ugdq uiqi ucrt'  # Paste the app password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'sahanac2024@gmail.com'
# THEN initialize Mail
mail = Mail(app)

# Rest of configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Image Upload Configuration
UPLOAD_FOLDER = 'static/uploads/items'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# PostgreSQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'lost_found_db',
    'user': 'postgres',
    'password': 'postgres123',
    'port': 5432
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    """Create database connection"""
    conn = psycopg.connect(**DB_CONFIG)
    return conn

# Your existing init_db() function stays the same...
# [Keep all your existing functions]

# Generate unique 8-character pickup code
def generate_pickup_code():
    """Generate a unique 8-character alphanumeric code"""
    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(characters, k=8))
    return code

# Send email to found person (reporter)
def send_email_to_finder(finder_email, finder_name, item_name, pickup_code):
    """Send email to the person who found the item"""
    try:
        subject = "Action Required: Item Claimed - Handover to Admin"
        
        body = f"""
Dear {finder_name},

Good news! The item you reported as FOUND has been successfully claimed and verified by our admin team.

Item Details: {item_name}

NEXT STEPS:
1. Please bring the item to the Admin Office
2. Hand over the item to the administrator
3. Provide this PICKUP CODE to the admin: {pickup_code}

IMPORTANT:
- Keep this code confidential
- The admin will verify this code before accepting the item
- Once handed over, you will receive a confirmation

Admin Office Hours: Monday-Friday, 9 AM - 5 PM
Location: [Your Admin Office Location]

Thank you for your honesty and cooperation!

Best regards,
Lost & Found Management Team

Pickup Code: {pickup_code}
"""
        
        msg = Message(
            subject=subject,
            recipients=[finder_email],
            body=body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        print(f"✓ Email sent to finder: {finder_email}")
        return True
    except Exception as e:
        print(f"✗ Failed to send email to finder: {str(e)}")
        return False

# Send email to lost person (claimant)
def send_email_to_claimer(claimer_email, claimer_name, item_name, pickup_code):
    """Send email to the person who claimed the item"""
    try:
        subject = "Great News! Your Claim Approved - Collect Your Item"
        
        body = f"""
Dear {claimer_name},

Excellent news! Your claim has been APPROVED by our admin team.

Item Details: {item_name}

NEXT STEPS TO COLLECT YOUR ITEM:
1. Visit the Admin Office during office hours
2. Provide this PICKUP CODE to the administrator: {pickup_code}
3. Bring a valid ID for verification
4. Collect your item

IMPORTANT:
- Keep this code confidential and secure
- You must provide this exact code to collect the item
- The item will be held for 7 days from today

Admin Office Hours: Monday-Friday, 9 AM - 5 PM
Location: [Your Admin Office Location]

Best regards,
Lost & Found Management Team

Pickup Code: {pickup_code}
"""
        
        msg = Message(
            subject=subject,
            recipients=[claimer_email],
            body=body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        print(f"✓ Email sent to claimer: {claimer_email}")
        return True
    except Exception as e:
        print(f"✗ Failed to send email to claimer: {str(e)}")
        return False

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    print("Creating PostgreSQL tables...")
    
    # User table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS "user" (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(10) NOT NULL CHECK(role IN ('user', 'admin'))
        )
    ''')
    print("✓ User table created")
    
    # Item table with image_path column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item (
            item_id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            category VARCHAR(100) NOT NULL,
            location VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'active' CHECK(status IN ('active', 'resolved', 'archived')),
            image_path VARCHAR(255)
        )
    ''')
    print("✓ Item table created")
    
    # Check if image_path column exists, if not add it
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'item' AND column_name = 'image_path'
    """)
    if not cursor.fetchone():
        print("Adding image_path column to item table...")
        cursor.execute('ALTER TABLE item ADD COLUMN image_path VARCHAR(255)')
        print("✓ image_path column added")
    
    # Report table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report (
            report_id SERIAL PRIMARY KEY,
            report_type VARCHAR(10) NOT NULL CHECK(report_type IN ('lost', 'found')),
            report_date TIMESTAMP NOT NULL,
            remarks TEXT,
            user_id INTEGER NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
            item_id INTEGER NOT NULL REFERENCES item(item_id) ON DELETE CASCADE
        )
    ''')
    print("✓ Report table created")
    
    # Claim_request table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claim_request (
            claim_id SERIAL PRIMARY KEY,
            claim_date TIMESTAMP NOT NULL,
            status VARCHAR(20) DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            proof TEXT NOT NULL,
            user_id INTEGER NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
            item_id INTEGER NOT NULL REFERENCES item(item_id) ON DELETE CASCADE
        )
    ''')
    print("✓ Claim_request table created")
    
    # Security_question table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_question (
            question_id SERIAL PRIMARY KEY,
            question_text TEXT NOT NULL,
            answer TEXT NOT NULL,
            claim_id INTEGER REFERENCES claim_request(claim_id) ON DELETE CASCADE,
            item_id INTEGER REFERENCES item(item_id) ON DELETE CASCADE
        )
    ''')
    print("✓ Security_question table created")
    
    # Admin_action table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_action (
            action_id SERIAL PRIMARY KEY,
            action_type VARCHAR(20) NOT NULL CHECK(action_type IN ('approve', 'reject')),
            remarks TEXT,
            timestamp TIMESTAMP NOT NULL,
            admin_id INTEGER NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
            claim_id INTEGER NOT NULL REFERENCES claim_request(claim_id) ON DELETE CASCADE
        )
    ''')
    print("✓ Admin_action table created")
    
    # Create default admin account
    cursor.execute('SELECT * FROM "user" WHERE email = %s', ('admin@admin.com',))
    if not cursor.fetchone():
        password_hash = generate_password_hash('admin123')
        cursor.execute(
            'INSERT INTO "user" (name, email, password_hash, role) VALUES (%s, %s, %s, %s)',
            ('Admin', 'admin@admin.com', password_hash, 'admin')
        )
        print("✓ Admin account created (Email: admin@admin.com, Password: admin123)")
    else:
        print("✓ Admin account already exists")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✓ All tables created successfully!")

# Decorator for role-based access control
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('index'))
            
            if role and session.get('role') != role:
                flash('Unauthorized access.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================
# PUBLIC ROUTES
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

# ============================================
# USER ROUTES
# ============================================

@app.route('/user/signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([name, email, password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('user_signup'))
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute('SELECT user_id FROM "user" WHERE email = %s', (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Email already registered. Please login.', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('user_login'))
        
        # Create new user
        password_hash = generate_password_hash(password)
        try:
            cursor.execute(
                'INSERT INTO "user" (name, email, password_hash, role) VALUES (%s, %s, %s, %s)',
                (name, email, password_hash, 'user')
            )
            conn.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('user_login'))
        except Exception as e:
            conn.rollback()
            flash(f'Error creating account: {str(e)}', 'error')
            return redirect(url_for('user_signup'))
        finally:
            cursor.close()
            conn.close()
    
    return render_template('user_signup.html')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            flash('Email and password are required.', 'error')
            return redirect(url_for('user_login'))
        
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM "user" WHERE email = %s AND role = %s', (email, 'user'))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session.permanent = True
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('user_login'))
    
    return render_template('user_login.html')

@app.route('/user/dashboard')
@login_required(role='user')
def user_dashboard():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get user info
    cursor.execute('SELECT * FROM "user" WHERE user_id = %s', (session['user_id'],))
    user = cursor.fetchone()
    
    # Get user's reports
    cursor.execute('''
        SELECT r.*, i.title, i.category, i.status, i.image_path
        FROM report r
        JOIN item i ON r.item_id = i.item_id
        WHERE r.user_id = %s
        ORDER BY r.report_date DESC
    ''', (session['user_id'],))
    reports = cursor.fetchall()
    
    # Get user's claims
    cursor.execute('''
        SELECT c.*, i.title, i.category, i.status, i.image_path
        FROM claim_request c
        JOIN item i ON c.item_id = i.item_id
        WHERE c.user_id = %s
        ORDER BY c.claim_date DESC
    ''', (session['user_id'],))
    claims = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('user_dashboard.html', user=user, reports=reports, claims=claims)

@app.route('/user/logout')
def user_logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

# ============================================
# ADMIN ROUTES
# ============================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            flash('Email and password are required.', 'error')
            return redirect(url_for('admin_login'))
        
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM "user" WHERE email = %s AND role = %s', (email, 'admin'))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            session.permanent = True
            session['user_id'] = admin['user_id']
            session['name'] = admin['name']
            session['email'] = admin['email']
            session['role'] = admin['role']
            flash(f'Welcome, Admin {admin["name"]}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'error')
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/api/keep-alive')
def keep_alive():
    """Endpoint to keep session alive"""
    if 'user_id' in session:
        return jsonify({'status': 'alive', 'user': session.get('name')})
    return jsonify({'status': 'expired'}), 401

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get admin info
    cursor.execute('SELECT * FROM "user" WHERE user_id = %s', (session['user_id'],))
    admin = cursor.fetchone()
    
    # Get statistics
    cursor.execute('SELECT COUNT(*) as count FROM report')
    total_reports = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM item')
    total_items = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM claim_request WHERE status = %s', ('pending',))
    pending_claims = cursor.fetchone()['count']
    
    # Get recent claims
    cursor.execute('''
        SELECT c.*, i.title, i.category, i.image_path, u.name as user_name
        FROM claim_request c
        JOIN item i ON c.item_id = i.item_id
        JOIN "user" u ON c.user_id = u.user_id
        ORDER BY c.claim_date DESC
        LIMIT 10
    ''')
    recent_claims = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_dashboard.html',
                         admin=admin,
                         total_reports=total_reports,
                         total_items=total_items,
                         pending_claims=pending_claims,
                         recent_claims=recent_claims)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Admin logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/claims')
@login_required(role='admin')
def admin_claims():
    """View all claim requests"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cursor.execute('''
            SELECT 
                c.claim_id,
                c.claim_date,
                c.status,
                c.proof,
                i.item_id,
                i.title,
                i.category,
                i.description,
                i.location,
                i.date,
                i.image_path,
                u.user_id,
                u.name as user_name,
                u.email as user_email
            FROM claim_request c
            JOIN item i ON c.item_id = i.item_id
            JOIN "user" u ON c.user_id = u.user_id
            ORDER BY 
                CASE c.status 
                    WHEN 'pending' THEN 1
                    WHEN 'approved' THEN 2
                    WHEN 'rejected' THEN 3
                END,
                c.claim_date DESC
        ''')
        
        claims = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('admin_claims.html', claims=claims)
        
    except Exception as e:
        print(f"Error loading claims: {str(e)}")
        cursor.close()
        conn.close()
        flash(f'Error loading claims: {str(e)}', 'danger')
        return render_template('admin_claims.html', claims=[])
    
@app.route('/admin/handover')
@login_required(role='admin')
def admin_handover():
    """Admin interface to manage item handovers"""
    return render_template('admin_handover.html')

@app.route('/admin/verify_handover', methods=['POST'])
@login_required(role='admin')
def verify_handover():
    """Admin verifies code when finder hands over item"""
    data = request.json
    pickup_code = data.get('pickup_code')
    
    conn = None
    cursor = None
    
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT claim_id, item_id 
            FROM claim_request 
            WHERE pickup_code = %s AND status = 'approved'
        """, (pickup_code,))
        
        claim = cursor.fetchone()
        
        if not claim:
            return jsonify({'error': 'Invalid pickup code or claim not approved'}), 404
        
        # Mark item as handed to admin
        cursor.execute("""
            UPDATE claim_request 
            SET item_handed_to_admin = TRUE,
                handed_to_admin_at = %s
            WHERE claim_id = %s
        """, (datetime.now(), claim['claim_id']))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item successfully received from finder!',
            'claim_id': claim['claim_id']
        }), 200
        
    except Exception as e:
        print(f"Error in verify_handover: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route('/admin/verify_collection', methods=['POST'])
@login_required(role='admin')
def verify_collection():
    """Admin verifies code when claimer collects item"""
    data = request.json
    pickup_code = data.get('pickup_code')
    
    conn = None
    cursor = None
    
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT claim_id, item_id, item_handed_to_admin
            FROM claim_request 
            WHERE pickup_code = %s AND status = 'approved'
        """, (pickup_code,))
        
        claim = cursor.fetchone()
        
        if not claim:
            return jsonify({'error': 'Invalid pickup code or claim not approved'}), 404
        
        # Check if item_handed_to_admin is True (handle NULL as False)
        if not claim.get('item_handed_to_admin'):
            return jsonify({'error': 'Item not yet received from finder. Please complete Step 1 first.'}), 400
        
        # Mark item as collected
        cursor.execute("""
            UPDATE claim_request 
            SET item_collected_by_claimer = TRUE,
                collected_at = %s
            WHERE claim_id = %s
        """, (datetime.now(), claim['claim_id']))
        
        # Mark item as resolved
        cursor.execute("""
            UPDATE item 
            SET status = 'resolved'
            WHERE item_id = %s
        """, (claim['item_id'],))  # Added missing comma for single-item tuple
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item successfully handed over to claimer! Case closed.',
            'claim_id': claim['claim_id']
        }), 200
        
    except Exception as e:
        print(f"Error in verify_collection: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
       
@app.route('/admin/claims/<int:claim_id>/review', methods=['GET', 'POST'])
@login_required(role='admin')
def review_claim(claim_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    if request.method == 'POST':
        action_type = request.form.get('action_type')
        remarks = request.form.get('remarks', '')
        
        try:
            # Update claim status
            new_status = 'approved' if action_type == 'approve' else 'rejected'
            
            cursor.execute(
                "UPDATE claim_request SET status = %s WHERE claim_id = %s",
                (new_status, claim_id)
            )
            
            # Insert into admin_action table
            cursor.execute(
                """INSERT INTO admin_action (action_type, remarks, timestamp, admin_id, claim_id) 
                   VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s)""",
                (action_type, remarks, session.get('user_id'), claim_id)
            )
            
            # Update item status if approved
            if action_type == 'approve':
                # Generate pickup code
                pickup_code = generate_pickup_code()
                
                # Ensure code is unique
                while True:
                    cursor.execute("SELECT claim_id FROM claim_request WHERE pickup_code = %s", (pickup_code,))
                    if not cursor.fetchone():
                        break
                    pickup_code = generate_pickup_code()
                
                # Update claim with pickup code
                cursor.execute(
                    'UPDATE claim_request SET pickup_code = %s WHERE claim_id = %s',
                    (pickup_code, claim_id)
                )
                
                # Get all necessary info for emails
                cursor.execute('''
                    SELECT 
                        c.item_id,
                        i.title as item_name,
                        r.user_id as reporter_id,
                        c.user_id as claimant_id
                    FROM claim_request c
                    JOIN item i ON c.item_id = i.item_id
                    JOIN report r ON r.item_id = i.item_id
                    WHERE c.claim_id = %s
                ''', (claim_id,))
                
                claim_info = cursor.fetchone()
                
                if claim_info:
                    # Get reporter (finder) details
                    cursor.execute(
                        'SELECT name, email FROM "user" WHERE user_id = %s',
                        (claim_info['reporter_id'],)
                    )
                    finder = cursor.fetchone()
                    
                    # Get claimant details
                    cursor.execute(
                        'SELECT name, email FROM "user" WHERE user_id = %s',
                        (claim_info['claimant_id'],)
                    )
                    claimer = cursor.fetchone()
                    
                    # Update item status
                    cursor.execute(
                        'UPDATE item SET status = %s WHERE item_id = %s',
                        ('resolved', claim_info['item_id'])
                    )
                    
                    # Commit before sending emails
                    conn.commit()
                    
                    # Send emails to both parties
                    send_email_to_finder(
                        finder_email=finder['email'],
                        finder_name=finder['name'],
                        item_name=claim_info['item_name'],
                        pickup_code=pickup_code
                    )

                    time.sleep(5)
                    
                    send_email_to_claimer(
                        claimer_email=claimer['email'],
                        claimer_name=claimer['name'],
                        item_name=claim_info['item_name'],
                        pickup_code=pickup_code
                    )
                    
                    flash(f'Claim approved! Emails sent with pickup code: {pickup_code}', 'success')
                else:
                    conn.commit()
                    flash('Claim approved but could not send emails.', 'warning')
            else:
                # For rejection, just commit
                conn.commit()
                flash(f'Claim has been {new_status} successfully!', 'success')
            
        except Exception as e:
            conn.rollback()
            flash(f'Error processing claim: {str(e)}', 'danger')
        
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('admin_claims'))
    
    # GET request - show the review page
    try:
        cursor.execute('''
            SELECT 
                cr.*,
                i.title, i.category, i.description, i.location, i.date, i.image_path,
                u.name as user_name, u.email as user_email
            FROM claim_request cr
            JOIN item i ON cr.item_id = i.item_id
            JOIN "user" u ON cr.user_id = u.user_id
            WHERE cr.claim_id = %s
        ''', (claim_id,))
        
        claim = cursor.fetchone()
        
        if not claim:
            flash('Claim not found', 'danger')
            return redirect(url_for('admin_claims'))
        
        cursor.close()
        conn.close()
        
        return render_template('review_claim.html', claim=claim)
        
    except Exception as e:
        print(f"Error loading claim: {str(e)}")
        cursor.close()
        conn.close()
        flash(f'Error loading claim: {str(e)}', 'danger')
        return redirect(url_for('admin_claims'))

# ============================================
# REPORT ROUTES
# ============================================

@app.route('/user/create-report', methods=['GET', 'POST'])
@login_required(role='user')
def create_report():
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')
        date = request.form.get('date')
        remarks = request.form.get('remarks')
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')
        
        if not all([report_type, title, description, category, location, date]):
            flash('All required fields must be filled.', 'error')
            return redirect(url_for('create_report'))
        
        if not security_question or not security_answer:
            flash('Security question and answer are required.', 'error')
            return redirect(url_for('create_report'))
        
        # Handle image upload
        image_filename = None
        if 'item_image' in request.files:
            file = request.files['item_image']
            
            # Check if file was actually selected
            if file and file.filename != '':
                if allowed_file(file.filename):
                    # Create secure filename with timestamp to avoid conflicts
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    original_filename = secure_filename(file.filename)
                    filename = f"{timestamp}_{original_filename}"
                    
                    # Save file
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_filename = filename
                else:
                    flash('Invalid file type. Please upload JPG, PNG, or GIF images only.', 'error')
                    return redirect(url_for('create_report'))
        
        conn = get_db()
        cursor = conn.cursor()
        try:
            # Create item first with image path
            cursor.execute(
                'INSERT INTO item (title, description, category, location, date, status, image_path) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING item_id',
                (title, description, category, location, date, 'active', image_filename)
            )
            item_id = cursor.fetchone()[0]
            
            # Create report
            cursor.execute(
                'INSERT INTO report (report_type, report_date, remarks, user_id, item_id) VALUES (%s, %s, %s, %s, %s) RETURNING report_id',
                (report_type, datetime.now(), remarks, session['user_id'], item_id)
            )
            report_id = cursor.fetchone()[0]
            
            # Store REPORTER's security question (claim_id = NULL, item_id set)
            cursor.execute(
                'INSERT INTO security_question (question_text, answer, claim_id, item_id) VALUES (%s, %s, %s, %s)',
                (security_question, security_answer, None, item_id)
            )
            
            conn.commit()
            flash(f'{report_type.capitalize()} item reported successfully!', 'success')
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            conn.rollback()
            # Delete uploaded image if database operation fails
            if image_filename:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                except:
                    pass
            flash(f'Error creating report: {str(e)}', 'error')
            return redirect(url_for('create_report'))
        finally:
            cursor.close()
            conn.close()
    
    return render_template('create_report.html')

@app.route('/user/items')
@login_required(role='user')
def view_items():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT i.*, r.report_type 
        FROM item i
        LEFT JOIN report r ON i.item_id = r.item_id
        WHERE i.status = %s
        ORDER BY i.date DESC
    ''', ('active',))
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('view_items.html', items=items)

# ============================================
# CLAIM ROUTES
# ============================================

@app.route('/user/submit-claim/<int:item_id>', methods=['GET', 'POST'])
@login_required(role='user')
def submit_claim(item_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    if request.method == 'POST':
        proof = request.form.get('proof')
        security_answer = request.form.get('security_answer')
        
        if not proof:
            flash('Proof description is required.', 'error')
            return redirect(url_for('submit_claim', item_id=item_id))
        
        if not security_answer:
            flash('Security answer is required.', 'error')
            return redirect(url_for('submit_claim', item_id=item_id))
        
        try:
            # Check if user already has a pending claim
            cursor.execute(
                'SELECT * FROM claim_request WHERE user_id = %s AND item_id = %s AND status = %s',
                (session['user_id'], item_id, 'pending')
            )
            existing_claim = cursor.fetchone()
            
            if existing_claim:
                flash('You already have a pending claim for this item.', 'error')
                return redirect(url_for('view_items'))
            
            # Create claim request
            cursor.execute(
                'INSERT INTO claim_request (claim_date, status, proof, user_id, item_id) VALUES (%s, %s, %s, %s, %s) RETURNING claim_id',
                (datetime.now(), 'pending', proof, session['user_id'], item_id)
            )
            claim_id = cursor.fetchone()['claim_id']
            
            # Get the reporter's security question
            cursor.execute(
                'SELECT question_text FROM security_question WHERE item_id = %s AND claim_id IS NULL LIMIT 1',
                (item_id,)
            )
            question = cursor.fetchone()
            
            # Store CLAIMANT's answer
            cursor.execute(
                'INSERT INTO security_question (question_text, answer, claim_id, item_id) VALUES (%s, %s, %s, %s)',
                (question['question_text'] if question else 'Security verification', security_answer, claim_id, item_id)
            )
            
            conn.commit()
            flash('Claim request submitted successfully!', 'success')
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            conn.rollback()
            flash(f'Error submitting claim: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()
            return redirect(url_for('submit_claim', item_id=item_id))
    
    # GET request - fetch item and security question
    cursor.execute('SELECT i.*, r.report_type FROM item i LEFT JOIN report r ON i.item_id = r.item_id WHERE i.item_id = %s', (item_id,))
    item = cursor.fetchone()
    
    # Get REPORTER's security question
    cursor.execute(
        'SELECT question_text FROM security_question WHERE item_id = %s AND claim_id IS NULL LIMIT 1',
        (item_id,)
    )
    security_question = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not item:
        flash('Item not found.', 'error')
        return redirect(url_for('view_items'))
    
    return render_template('claim_form.html', item=item, security_question=security_question)

@app.route('/user/my-claims')
@login_required(role='user')
def my_claims():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT c.*, i.title, i.category, i.description, i.image_path
        FROM claim_request c
        JOIN item i ON c.item_id = i.item_id
        WHERE c.user_id = %s
        ORDER BY c.claim_date DESC
    ''', (session['user_id'],))
    claims = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('my_claims.html', claims=claims)

@app.route('/admin/reports')
@login_required(role='admin')
def admin_reports():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT r.*, i.title, i.category, i.status, i.image_path, u.name as user_name
        FROM report r
        JOIN item i ON r.item_id = i.item_id
        JOIN "user" u ON r.user_id = u.user_id
        ORDER BY r.report_date DESC
    ''')
    reports = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin_reports.html', reports=reports)

@app.route('/admin/actions')
@login_required(role='admin')
def admin_actions():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cursor.execute('''
            SELECT 
                aa.action_id,
                aa.claim_id,
                aa.action_type,
                aa.remarks,
                aa.timestamp,
                u.name as admin_name,
                u.email as admin_email,
                i.title as item_title,
                i.category as item_category,
                i.image_path,
                c.status as claim_status,
                claimant.name as claimant_name,
                claimant.email as claimant_email
            FROM admin_action aa
            LEFT JOIN "user" u ON aa.admin_id = u.user_id
            LEFT JOIN claim_request c ON aa.claim_id = c.claim_id
            LEFT JOIN item i ON c.item_id = i.item_id
            LEFT JOIN "user" claimant ON c.user_id = claimant.user_id
            ORDER BY aa.timestamp DESC
        ''')
        
        actions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('admin_actions.html', actions=actions)
        
    except Exception as e:
        print(f"✗ Error in admin_actions: {str(e)}")
        cursor.close()
        conn.close()
        flash(f'Error loading actions: {str(e)}', 'danger')
        return render_template('admin_actions.html', actions=[])

@app.route('/api/get-security-answers/<int:claim_id>')
@login_required(role='admin')
def get_security_answers(claim_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Get item_id from claim
        cursor.execute('SELECT item_id FROM claim_request WHERE claim_id = %s', (claim_id,))
        claim = cursor.fetchone()
        
        if not claim:
            return jsonify({'success': False, 'error': 'Claim not found'}), 404
        
        item_id = claim['item_id']
        
        # Get REPORTER's security question and answer
        cursor.execute('''
            SELECT question_text, answer 
            FROM security_question 
            WHERE item_id = %s AND claim_id IS NULL
            LIMIT 1
        ''', (item_id,))
        reporter_security = cursor.fetchone()
        
        # Get CLAIMANT's answer
        cursor.execute('''
            SELECT question_text, answer 
            FROM security_question 
            WHERE claim_id = %s
            LIMIT 1
        ''', (claim_id,))
        claimant_security = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'reporter_question': reporter_security['question_text'] if reporter_security else 'N/A',
            'reporter_answer': reporter_security['answer'] if reporter_security else 'N/A',
            'claimant_answer': claimant_security['answer'] if claimant_security else 'N/A'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Route to serve uploaded images
@app.route('/uploads/items/<filename>')
def uploaded_file(filename):
    """Serve uploaded item images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/debug/claim/<int:claim_id>')
@login_required(role='admin')
def debug_single_claim(claim_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('''
        SELECT 
            cr.claim_id,
            cr.item_id,
            cr.proof,
            cr.status,
            i.title,
            i.description,
            u.name as user_name
        FROM claim_request cr
        JOIN item i ON cr.item_id = i.item_id
        JOIN "user" u ON cr.user_id = u.user_id
        WHERE cr.claim_id = %s
    ''', (claim_id,))
    
    claim = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if claim:
        return f"""
        <h1>Debug Claim #{claim_id}</h1>
        <p><strong>Claim ID:</strong> {claim['claim_id']}</p>
        <p><strong>Item ID:</strong> {claim['item_id']}</p>
        <p><strong>Title:</strong> {claim['title']}</p>
        <p><strong>Description:</strong> {claim['description']}</p>
        <p><strong>User:</strong> {claim['user_name']}</p>
        <p><strong>Status:</strong> {claim['status']}</p>
        """
    else:
        return f"<h1>No claim found with ID {claim_id}</h1>"
@app.route('/admin/test-email')
@login_required(role='admin')
def test_email():
    """Test route to verify email configuration"""
    try:
        msg = Message(
            subject='Test Email from Lost & Found System',
            recipients=['sahanac2024@gmail.com'],  # Send to yourself for testing
            body='This is a test email. If you receive this, your email configuration is working correctly!',
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        print("✓ Test email sent successfully!")
        flash('Test email sent successfully! Check your inbox.', 'success')
    except Exception as e:
        print(f"✗ Failed to send test email: {str(e)}")
        flash(f'Failed to send test email: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)