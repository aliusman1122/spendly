import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db, get_user_by_email, get_user_by_id

app = Flask(__name__)
app.secret_key = os.urandom(24)
csrf = CSRFProtect(app)
app.config["WTF_CSRF_TIME_LIMIT"] = None


@app.before_request
def before_request():
    user_id = session.get("user_id")
    if user_id:
        user = get_user_by_id(user_id)
        if user:
            session["user_name"] = user["name"]
        else:
            session.clear()
    else:
        session.pop("user_name", None)


with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(name) < 2:
            return render_template("register.html", error="Name must be at least 2 characters")
        if "@" not in email or "." not in email:
            return render_template("register.html", error="Please enter a valid email address")
        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters")
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        existing_user = get_user_by_email(email)
        if existing_user:
            return render_template("register.html", error="Email already registered")

        password_hash = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            conn.commit()
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("profile"))
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    # Redirect if not logged in
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Hardcoded data for UI design (will be replaced with DB queries in Step 5)
    user = {
        "name": "Alex Morgan",
        "email": "alex@example.com",
        "member_since": "January 2025"
    }

    stats = {
        "total_spent": 45750,
        "transaction_count": 24,
        "top_category": "Food & Dining"
    }

    transactions = [
        {"date": "2025-05-15", "description": "Swiggy order", "category": "Food", "amount": 450},
        {"date": "2025-05-14", "description": "Metro recharge", "category": "Transport", "amount": 200},
        {"date": "2025-05-13", "description": "Amazon purchase", "category": "Shopping", "amount": 1299},
    ]

    categories = [
        {"name": "Food & Dining", "amount": 18500, "color": "food"},
        {"name": "Transport", "amount": 8200, "color": "transport"},
        {"name": "Shopping", "amount": 12000, "color": "shopping"},
    ]

    # Calculate max for progress bars
    max_category_amount = max(cat["amount"] for cat in categories)

    return render_template("profile.html",
                         user=user,
                         stats=stats,
                         transactions=transactions,
                         categories=categories,
                         max_category_amount=max_category_amount)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
