# Newspaper Admin Authentication - Implementation Guide

## Current Status

**Development Environment:** No authentication - all admin routes are open access

**Production Requirement:** Flask-Login authentication must be implemented before staging/production deployment

---

## Flask-Login Implementation Checklist

### 1. Install Dependencies

```bash
pip install flask-login
# Update requirements.txt
echo "flask-login>=0.6.3" >> requirements.txt
```

### 2. Create User Model

**File:** `web/app/models/user.py`

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from .base import BaseModel

class User(BaseModel, UserMixin):
    """User accounts for admin access"""
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Roles
    is_admin = Column(Boolean, default=False)
    is_editor = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"
```

### 3. Create Database Migration

```sql
-- File: etl/sql/migrations/003_create_users_table.sql

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_editor BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Create initial admin user (change password immediately!)
INSERT INTO users (username, email, password_hash, is_admin, is_active)
VALUES (
    'admin',
    'admin@branchbaseball.local',
    -- Password: 'changeme' (CHANGE THIS!)
    'pbkdf2:sha256:600000$...',  -- Use User.set_password() to generate
    TRUE,
    TRUE
);
```

### 4. Create Auth Blueprint

**File:** `web/app/routes/auth.py`

```python
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.models import User
from app.extensions import db

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()

            next_page = request.args.get('next')
            return redirect(next_page or url_for('newspaper_admin.draft_list'))

        flash('Invalid username or password', 'error')

    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
```

### 5. Initialize Flask-Login

**File:** `web/app/__init__.py`

```python
from flask_login import LoginManager

def create_app(config_name='development'):
    app = Flask(__name__)
    # ... existing setup ...

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Register auth blueprint
    from .routes import auth
    app.register_blueprint(auth.bp, url_prefix='/auth')

    return app
```

### 6. Update Admin Decorator

**File:** `web/app/routes/newspaper_admin.py`

```python
from flask_login import login_required, current_user
from flask import abort

def admin_required(f):
    """Require admin role"""
    from functools import wraps

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)

    return decorated_function

# Optional: Editor role for less privileged access
def editor_required(f):
    """Require editor or admin role"""
    from functools import wraps

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_admin or current_user.is_editor):
            abort(403)
        return f(*args, **kwargs)

    return decorated_function
```

### 7. Create Login Template

**File:** `web/app/templates/auth/login.html`

```html
{% extends "base.html" %}

{% block title %}Login - Admin{% endblock %}

{% block content %}
<div class="max-w-md mx-auto mt-16">
    <div class="bg-white rounded-lg shadow-lg border-2 border-leather p-8">
        <h1 class="text-3xl font-bold text-forest deco-heading mb-6 text-center">
            Admin Login
        </h1>

        <form method="POST">
            <div class="mb-4">
                <label for="username" class="block text-sm font-semibold text-forest mb-2">
                    Username
                </label>
                <input type="text" id="username" name="username" required
                       class="w-full px-4 py-2 border-2 border-tan rounded-lg focus:border-forest focus:outline-none">
            </div>

            <div class="mb-6">
                <label for="password" class="block text-sm font-semibold text-forest mb-2">
                    Password
                </label>
                <input type="password" id="password" name="password" required
                       class="w-full px-4 py-2 border-2 border-tan rounded-lg focus:border-forest focus:outline-none">
            </div>

            <button type="submit"
                    class="w-full bg-forest text-cream py-3 rounded-lg hover:bg-forest-dark transition-colors font-medium">
                Log In
            </button>
        </form>
    </div>
</div>
{% endblock %}
```

### 8. Create Admin User Script

**File:** `web/scripts/create_admin.py`

```python
#!/usr/bin/env python3
"""Create an admin user for the newspaper system"""
import sys
sys.path.insert(0, '/mnt/hdd/PycharmProjects/rb2/web')

from app import create_app
from app.models import User
from app.extensions import db
import getpass

app = create_app()

with app.app_context():
    username = input("Username: ")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    password2 = getpass.getpass("Confirm Password: ")

    if password != password2:
        print("Passwords don't match!")
        sys.exit(1)

    if User.query.filter_by(username=username).first():
        print(f"User '{username}' already exists!")
        sys.exit(1)

    user = User(
        username=username,
        email=email,
        is_admin=True,
        is_active=True
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    print(f"✅ Admin user '{username}' created successfully!")
```

Make executable:
```bash
chmod +x web/scripts/create_admin.py
```

---

## Deployment Steps

### For Staging Deployment:

1. Run database migration to create `users` table
2. Run `python web/scripts/create_admin.py` to create admin account
3. Update `web/app/__init__.py` to initialize Flask-Login
4. Update `web/app/routes/newspaper_admin.py` decorator
5. Deploy and test login flow
6. **IMPORTANT:** Change default admin password immediately

### For Production Deployment:

All staging steps, plus:

7. Set strong `SECRET_KEY` in environment variables
8. Enable HTTPS (required for secure session cookies)
9. Set `SESSION_COOKIE_SECURE = True` in production config
10. Set `SESSION_COOKIE_HTTPONLY = True`
11. Consider adding 2FA for admin accounts
12. Set up password reset flow (optional)
13. Monitor failed login attempts

---

## Security Considerations

### Session Security
- Use strong `SECRET_KEY` (32+ random bytes)
- Set secure cookie flags in production
- Configure session timeout (default: browser close)

### Password Policy
- Minimum 12 characters recommended
- Require complexity (upper, lower, numbers, symbols)
- Hash with werkzeug's default (PBKDF2-SHA256)

### Additional Hardening
- Rate limit login attempts (Flask-Limiter)
- Log all admin actions
- Implement CSRF protection (Flask-WTF)
- Regular security audits

---

## Testing Authentication

```python
# Test user creation
python web/scripts/create_admin.py

# Test login flow
# Visit: http://localhost:5001/auth/login
# Try: correct credentials → should redirect to /newspaper/admin/drafts
# Try: wrong credentials → should show error message

# Test protected routes
# Visit: http://localhost:5001/newspaper/admin/drafts (not logged in)
# Should redirect to login page with "next" parameter

# Test logout
# Visit: http://localhost:5001/auth/logout
# Should redirect to homepage
```

---

## Current Workaround (Development Only)

For development, admin routes are currently **open to all users**. The `@admin_required` decorator is a no-op:

```python
# Current implementation (development only)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)  # No auth check!
    return decorated_function
```

**⚠️ WARNING:** Do not deploy to staging or production without implementing proper authentication!

---

## Questions?

- Flask-Login docs: https://flask-login.readthedocs.io/
- Werkzeug password hashing: https://werkzeug.palletsprojects.com/en/latest/utils/#werkzeug.security.generate_password_hash
- Flask session security: https://flask.palletsprojects.com/en/latest/security/

---

**Last Updated:** 2025-10-20
**Status:** Not yet implemented - deferred for staging/production
