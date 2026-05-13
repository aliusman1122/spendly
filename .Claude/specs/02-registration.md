---
name: 02-registration
description: User registration with email/password and session management
metadata:
  type: feature
---

# Spec: Registration

## Overview
Implements user registration functionality allowing new users to create accounts with name, email, and password. Includes form validation, password hashing with werkzeug, and session-based login after successful registration. This is Step 2 of the Spendly teaching roadmap.

## Depends on
- Step 1: Database setup (complete - users table exists)

## Routes

| Route | Method | Description | Access |
|-------|--------|-------------|--------|
| `/register` | GET | Registration form | Public |
| `/register` | POST | Create new user | Public |
| `/login` | GET | Login form (modify for backend integration) | Public |
| `/login` | POST | Authenticate user and start session | Public |
| `/logout` | GET/POST | Clear session and redirect | Logged-in |

## Database changes
No database changes required for this step. The `users` table already exists with the necessary schema.

## Templates

### Modify
- `templates/register.html` — Add form with POST method, CSRF protection (if applicable), name/email/password fields, and placeholder for validation errors.
- `templates/login.html` — Add form with POST method, CSRF protection, email/password fields, and login error handling.

## Files to change
- `app.py` — Add `/register`, `/login`, and `/logout` routes with authentication and session logic.

## Files to create
None.

## New dependencies
No new dependencies (Flask session, werkzeug are already available in the environment).

## Rules for implementation
- No SQLAlchemy or ORMs — use parameterized SQL queries only via sqlite3.
- Passwords must be securely hashed with `werkzeug.security.generate_password_hash`.
- Use `werkzeug.security.check_password_hash` for login verification.
- Use Flask `session` for user login management.
- Use CSS variables from `static/css/style.css` — never hardcode hex values.
- All templates must extend `base.html`.
- Validate email format and uniqueness (check if email already exists in the database).
- Password must be a minimum of 6 characters.
- Name is required, with a minimum of 2 characters.

## Definition of done
- [ ] GET /register displays registration form with name, email, and password fields.
- [ ] POST /register creates a new user in the database with a hashed password and redirects to login or dashboard.
- [ ] Duplicate email submission shows the specific error: "Email already registered".
- [ ] GET /login displays the login form.
- [ ] POST /login authenticates the user, sets the Flask session, and redirects to the home/dashboard page.
- [ ] Invalid login credentials show the error: "Invalid email or password".
- [ ] Logged-in users trying to access `/login` or `/register` are automatically redirected away.
- [ ] Accessing `/logout` clears the session and redirects to `/login`.