# Lost & Found Management System

A secure, web-based platform designed to help users report lost or found items and verify ownership through a structured admin-mediated claim process.

---

##  Features

### For Users

- **User Authentication**: Secure signup and login system
- **Report Items**: Create detailed reports for lost or found items, including categories, locations, and dates
- **Security Questions**: Reporters set a specific security question that only the true owner should know
- **Browse Items**: View a live feed of all active lost and found reports
- **Claim System**: Submit claims for found items by providing proof of ownership and answering the reporter's security question
- **Personal Dashboard**: Track the status of your reports and submitted claims

### For Administrators

- **Admin Dashboard**: Overview of system statistics (Total reports, items, and pending claims)
- **Claim Review**: Dedicated interface to compare the reporter's answer with the claimant's answer
- **Action History**: A log of all approved and rejected claims with admin remarks
- **Database Management**: Automated status updates (e.g., marking items as 'Resolved' upon approved claims)

---

##  Tech Stack

- **Backend**: Python (Flask)
- **Database**: PostgreSQL (for production/primary use), SQLite (support included)
- **Frontend**: HTML5, CSS3 (Modern, responsive UI)
- **Authentication**: Werkzeug (Password Hashing)
- **Database Tooling**: Psycopg2

---

##  Prerequisites

- Python 3.12+
- PostgreSQL installed and running
- Git

---

##  Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Lost-Found-Management.git
cd Lost-Found-Management
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirement.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/lost_found_db
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```

### 5. Initialize the Database

Run the application once to trigger `init_db()` or run the models script:

```bash
python models.py init
```

> **Note**: A default admin account is created automatically:
> - **Email**: admin@admin.com
> - **Password**: admin123

---

##  Running the Application

```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000`.

---

##  Project Structure

- **app.py**: Main Flask application routes and logic
- **models.py**: Database schemas and helper functions
- **templates/**: HTML templates for User and Admin interfaces
- **static/**: CSS styles and client-side assets
- **fix_security_table.py**: Migration script for database schema updates

---

##  Security Features

- **Role-Based Access Control (RBAC)**: Routes are protected using a `@login_required` decorator to ensure users cannot access admin panels
- **Ownership Validation**: Claims require a two-step verification—written proof and a matching security answer
- **Session Security**: Configured with `SESSION_COOKIE_HTTPONLY` and `SAMESITE` protections

---

##  Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

##  License

Distributed under the MIT License. See LICENSE for more information.

---

##  Deploying to GitHub

### Steps to push to GitHub:

1. Go to GitHub and create a new repository named `Lost-Found-Management`

2. In your terminal, run:

```bash
git init
git add .
git commit -m "Initial commit: Lost and Found Management System"
git branch -M main
git remote add origin https://github.com/your-username/Lost-Found-Management.git
git push -u origin main
```

---

##  Support

For issues, questions, or suggestions, please open an issue on the GitHub repository.

---

**Happy coding! **
