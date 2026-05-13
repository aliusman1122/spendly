# Spendly - Expense Tracker

A Flask-based expense tracking web application built as a teaching project for students.

## Tech Stack

- **Backend**: Flask 3.1.3, Werkzeug 3.1.6
- **Database**: SQLite (via `database/db.py` - to be implemented by students)
- **Testing**: pytest 8.3.5, pytest-flask 1.3.0
- **Frontend**: HTML templates with Jinja2, vanilla JavaScript, CSS

## Project Structure

```
expense-tracker/
├── app.py              # Main Flask application with routes
├── requirements.txt    # Python dependencies
├── database/
│   ├── __init__.py    # Package init
│   └── db.py          # Database utilities (stub - students implement)
├── templates/
│   ├── base.html      # Base template with navbar/footer
│   ├── landing.html   # Landing page with hero, features, CTA
│   ├── login.html     # Login form
│   ├── register.html  # Registration form
│   ├── terms.html     # Terms and conditions
│   └── privacy.html   # Privacy policy
├── static/
│   ├── css/
│   │   ├── style.css  # Global styles
│   │   └── landing.css # Landing page styles
│   └── js/
│       └── main.js    # Frontend JavaScript (stub for features)
└── myenv/             # Python virtual environment (gitignored)
```

## Routes

| Route | Method | Description | Status |
|-------|--------|-------------|--------|
| `/` | GET | Landing page | Implemented |
| `/register` | GET | Registration page | Implemented |
| `/login` | GET | Login page | Implemented |
| `/terms` | GET | Terms and conditions | Implemented |
| `/privacy` | GET | Privacy policy | Implemented |
| `/logout` | GET | Logout action | Placeholder |
| `/profile` | GET | User profile | Placeholder |
| `/expenses/add` | GET/POST | Add expense | Placeholder |
| `/expenses/<id>/edit` | GET/POST | Edit expense | Placeholder |
| `/expenses/<id>/delete` | POST | Delete expense | Placeholder |

## Database Schema (To Implement)

The `database/db.py` file needs to implement:

- `get_db()` - Returns SQLite connection with row_factory and foreign keys enabled
- `init_db()` - Creates tables using CREATE TABLE IF NOT EXISTS
- `seed_db()` - Inserts sample development data

Expected tables based on app requirements:
- `users` - User accounts (id, email, password_hash, name, created_at)
- `expenses` - Expense records (id, user_id, amount, category, description, date, created_at)
- `categories` - Expense categories (id, user_id, name, color, icon)

## Running the Application

```bash
# Activate virtual environment
myenv\Scripts\activate  # Windows
source myenv/bin/activate  # Unix

# Install dependencies
pip install -r requirements.txt

# Run the development server
python app.py  # Runs on http://localhost:5001
```

## Testing

```bash
pytest  # Run all tests
pytest -v  # Verbose output
```

## Development Notes

- This is a teaching project - students implement features incrementally (Steps 1-9+)
- Database layer is intentionally left as a stub for students to complete
- Uses Indian Rupee (₹) as the default currency symbol
- Port 5001 is used instead of default 5000 to avoid conflicts
