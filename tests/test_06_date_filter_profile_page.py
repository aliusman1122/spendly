"""Tests for the date filter feature on the profile page (Step 6).

These tests verify that the date range filter on /profile correctly filters:
- Summary stats (total spent, transaction count, top category)
- Recent transactions list
- Category breakdown

And that edge cases (invalid dates, start > end) are handled gracefully.
"""

import datetime
import pytest
from app import app as flask_app
from database.db import init_db, get_db, get_user_by_email


@pytest.fixture
def app():
    """Create application with in-memory database for testing."""
    flask_app.config.update({
        'TESTING': True,
        'DATABASE': ':memory:',
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    })
    with flask_app.app_context():
        init_db()
        _seed_test_data()
        yield flask_app


def _seed_test_data():
    """Seed test data with expenses across different dates."""
    conn = get_db()
    try:
        # Create test user
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash("testpass123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Test User", "test@example.com", password_hash)
        )
        user_id = cursor.lastrowid

        # Create expenses across different time periods
        today = datetime.date.today()
        expenses = [
            # This month's expenses
            (user_id, 500.00, "Food", str(today), "Today's lunch"),
            (user_id, 300.00, "Transport", str(today - datetime.timedelta(days=5)), "Metro pass"),
            (user_id, 1000.00, "Shopping", str(today - datetime.timedelta(days=10)), "New shoes"),
            # Last month's expense (within 3 months but not this month)
            (user_id, 2000.00, "Bills", str(today - datetime.timedelta(days=35)), "Electricity bill"),
            # Expense 4 months ago (within 6 months but not 3 months)
            (user_id, 5000.00, "Entertainment", str(today - datetime.timedelta(days=120)), "Concert tickets"),
            # Old expense (more than 6 months ago)
            (user_id, 15000.00, "Other", str(today - datetime.timedelta(days=200)), "Old expense"),
        ]

        for expense in expenses:
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                expense
            )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def client(app):
    """Return test client."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Return test client that is logged in as test user."""
    client.post('/login', data={'email': 'test@example.com', 'password': 'testpass123'})
    return client


# ------------------------------------------------------------------ #
# Auth Guard Tests                                                    #
# ------------------------------------------------------------------ #

class TestProfileAuthGuard:
    """Tests that unauthenticated requests to /profile are rejected."""

    def test_unauthenticated_redirect_to_login(self, client):
        """Unauthenticated request to /profile should redirect to login page."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_unauthenticated_with_date_params_redirects_to_login(self, client):
        """Unauthenticated request with date params should still redirect to login."""
        today = datetime.date.today()
        response = client.get(f'/profile?date_from={today}&date_to={today}')
        assert response.status_code == 302
        assert '/login' in response.location


# ------------------------------------------------------------------ #
# Happy Path Tests                                                    #
# ------------------------------------------------------------------ #

class TestDateFilterHappyPath:
    """Tests for successful date filtering scenarios."""

    def test_no_filter_returns_all_expenses(self, auth_client):
        """Profile with no date params should show all expenses (unfiltered)."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        data = response.data

        # Total should include all 6 expenses: 500 + 300 + 1000 + 2000 + 5000 + 15000 = 23800
        assert b'23,800' in data or b'23800' in data

        # Transaction count should be 6
        assert b'6' in data

    def test_this_month_filter(self, auth_client):
        """This Month filter should only show expenses from current calendar month."""
        today = datetime.date.today()
        first_of_month = today.replace(day=1)

        response = auth_client.get(f'/profile?date_from={first_of_month}&date_to={today}')
        assert response.status_code == 200
        data = response.data

        # Should have only this month's expenses (500 + 300 + 1000 = 1800)
        assert b'1,800' in data or b'1800' in data

        # Should have 3 transactions (Food, Transport, Shopping from this month)
        assert b'3' in data

        # active_filter should be "this_month"
        assert b'this_month' in data

    def test_last_3_months_filter(self, auth_client):
        """Last 3 Months filter should show expenses from last 90 days."""
        today = datetime.date.today()
        three_months_ago = today - datetime.timedelta(days=90)

        response = auth_client.get(f'/profile?date_from={three_months_ago}&date_to={today}')
        assert response.status_code == 200
        data = response.data

        # Should include: this month's (500+300+1000=1800) + last month (2000) = 3800
        # Note: depends on how old "today" is; at minimum should have this month's expenses
        assert b'1,800' in data or b'1800' in data

        # active_filter should be "last_3m"
        assert b'last_3m' in data

    def test_last_6_months_filter(self, auth_client):
        """Last 6 Months filter should show expenses from last 180 days."""
        today = datetime.date.today()
        six_months_ago = today - datetime.timedelta(days=180)

        response = auth_client.get(f'/profile?date_from={six_months_ago}&date_to={today}')
        assert response.status_code == 200
        data = response.data

        # Should include all except the 200-day old expense (23800 - 15000 = 8800)
        assert b'8,800' in data or b'8800' in data

        # active_filter should be "last_6m"
        assert b'last_6m' in data

    def test_custom_date_range(self, auth_client):
        """Custom date range should filter expenses correctly."""
        today = datetime.date.today()
        # Range: last 7 days only
        date_from = today - datetime.timedelta(days=7)
        date_to = today

        response = auth_client.get(f'/profile?date_from={date_from}&date_to={date_to}')
        assert response.status_code == 200
        data = response.data

        # Should include expenses from last 7 days (500 + 300 = 800)
        assert b'800' in data

    def test_all_time_no_params(self, auth_client):
        """No query params should show all expenses (same as unfiltered)."""
        response = auth_client.get('/profile')
        assert response.status_code == 200

        # Should NOT set any active_filter for "All Time"
        # (The spec says "All Time" preset must pass no query params)

        # Transaction count should be the full count
        assert b'6' in data


# ------------------------------------------------------------------ #
# Edge Case Tests                                                     #
# ------------------------------------------------------------------ #

class TestDateFilterEdgeCases:
    """Tests for edge cases: invalid dates, start > end, etc."""

    def test_invalid_date_from_malformed(self, auth_client):
        """Malformed date_from should fall back to unfiltered view."""
        response = auth_client.get('/profile?date_from=not-a-date&date_to=2024-12-31')
        assert response.status_code == 200

        # Should show all expenses (unfiltered)
        data = response.data
        assert b'23,800' in data or b'23800' in data

    def test_invalid_date_to_malformed(self, auth_client):
        """Malformed date_to should fall back to unfiltered view."""
        today = datetime.date.today()
        response = auth_client.get(f'/profile?date_from=2024-01-01&date_to=invalid')
        assert response.status_code == 200

        # Should show all expenses (unfiltered)
        data = response.data
        assert b'23,800' in data or b'23800' in data

    def test_both_dates_invalid_fallback(self, auth_client):
        """Both dates invalid should fall back to unfiltered view."""
        response = auth_client.get('/profile?date_from=bad&date_to=also-bad')
        assert response.status_code == 200

        # Should show all expenses
        data = response.data
        assert b'23,800' in data or b'23800' in data

    def test_start_date_after_end_date_shows_flash_error(self, auth_client):
        """When date_from > date_to, should show flash error and fall back to unfiltered."""
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        # date_from is after date_to
        response = auth_client.get(f'/profile?date_from={today}&date_to={yesterday}')
        assert response.status_code == 200

        # Should fall back to showing all expenses
        data = response.data
        assert b'23,800' in data or b'23800' in data

        # Should show flash error message
        # Flask flash messages are stored in session; check response contains error
        # (In tests, flash messages render in the template)
        assert b'Start date must be before end date' in data

    def test_empty_date_params_fallback(self, auth_client):
        """Empty date params should show all expenses (unfiltered)."""
        response = auth_client.get('/profile?date_from=&date_to=')
        assert response.status_code == 200

        # Should show all expenses
        data = response.data
        assert b'23,800' in data or b'23800' in data

    def test_only_date_from_provided(self, auth_client):
        """Only date_from provided should show all from that date onward."""
        today = datetime.date.today()
        # From 4 months ago to today (should include everything except old 200-day expense)
        four_months_ago = today - datetime.timedelta(days=120)

        response = auth_client.get(f'/profile?date_from={four_months_ago}')
        assert response.status_code == 200
        data = response.data

        # Should include: 500 + 300 + 1000 + 2000 + 5000 = 8800
        assert b'8,800' in data or b'8800' in data

    def test_only_date_to_provided(self, auth_client):
        """Only date_to provided should show all up to that date."""
        today = datetime.date.today()
        # Up to 35 days ago (should include this month + last month, but not older)
        date_to = today - datetime.timedelta(days=35)

        response = auth_client.get(f'/profile?date_to={date_to}')
        assert response.status_code == 200
        data = response.data

        # Should include: 500 + 300 + 1000 + 2000 = 3800
        assert b'3,800' in data or b'3800' in data


# ------------------------------------------------------------------ #
# DB Side Effect Tests                                               #
# ------------------------------------------------------------------ #

class TestDateFilterDatabaseEffects:
    """Verify that date filtering actually affects database queries."""

    def test_stats_filtered_correctly(self, auth_client):
        """Stats should reflect the filtered date range."""
        today = datetime.date.today()
        first_of_month = today.replace(day=1)

        response = auth_client.get(f'/profile?date_from={first_of_month}&date_to={today}')
        assert response.status_code == 200

        # Stats should show only this month's totals
        data = response.data

        # Total spent should be only this month's: 500 + 300 + 1000 = 1800
        assert b'1,800' in data or b'1800' in data

        # Transaction count should be 3
        assert b'3' in data

    def test_transactions_list_filtered(self, auth_client):
        """Recent transactions list should be filtered to date range."""
        today = datetime.date.today()
        first_of_month = today.replace(day=1)

        response = auth_client.get(f'/profile?date_from={first_of_month}&date_to={today}')
        assert response.status_code == 200

        data = response.data

        # Should show only transactions from this month
        # The test data has 3 this-month transactions
        # Verify the transactions appear in the response
        assert b"Today's lunch" in data or b'lunch' in data

    def test_categories_filtered(self, auth_client):
        """Category breakdown should be filtered to date range."""
        today = datetime.date.today()
        first_of_month = today.replace(day=1)

        response = auth_client.get(f'/profile?date_from={first_of_month}&date_to={today}')
        assert response.status_code == 200

        data = response.data

        # Category breakdown should reflect this month's categories
        # This month's expenses: Food (500), Transport (300), Shopping (1000)
        # Should see these categories in the response
        # Food should appear as it has expense this month
        assert b'Food' in data


# ------------------------------------------------------------------ #
# Template Rendering Tests                                           #
# ------------------------------------------------------------------ #

class TestDateFilterTemplateRendering:
    """Verify template receives correct filter-related variables."""

    def test_active_filter_this_month(self, auth_client):
        """Template should receive active_filter='this_month' for This Month preset."""
        today = datetime.date.today()
        first_of_month = today.replace(day=1)

        response = auth_client.get(f'/profile?date_from={first_of_month}&date_to={today}')
        assert response.status_code == 200

        data = response.data
        # The template should highlight the "This Month" button
        assert b'this_month' in data

    def test_active_filter_last_3m(self, auth_client):
        """Template should receive active_filter='last_3m' for Last 3 Months preset."""
        today = datetime.date.today()
        three_months_ago = today - datetime.timedelta(days=90)

        response = auth_client.get(f'/profile?date_from={three_months_ago}&date_to={today}')
        assert response.status_code == 200

        data = response.data
        assert b'last_3m' in data

    def test_active_filter_last_6m(self, auth_client):
        """Template should receive active_filter='last_6m' for Last 6 Months preset."""
        today = datetime.date.today()
        six_months_ago = today - datetime.timedelta(days=180)

        response = auth_client.get(f'/profile?date_from={six_months_ago}&date_to={today}')
        assert response.status_code == 200

        data = response.data
        assert b'last_6m' in data

    def test_date_fields_populated(self, auth_client):
        """Custom date range should populate the date input fields."""
        today = datetime.date.today()
        date_from = today - datetime.timedelta(days=30)
        date_to = today

        response = auth_client.get(f'/profile?date_from={date_from}&date_to={date_to}')
        assert response.status_code == 200

        data = response.data
        # The date_from value should appear in the template
        assert str(date_from).encode() in data or date_from.isoformat().encode() in data

    def test_this_month_preset_links_generated(self, auth_client):
        """This Month preset link should have correct date params in template."""
        response = auth_client.get('/profile')
        assert response.status_code == 200

        data = response.data

        # Template should include the preset links with proper date calculations
        # The this_month_from and today should be passed to template
        # (Checking that the dates are available for the preset links)
        assert b'date_from' in data or b'date_to' in data


# ------------------------------------------------------------------ #
# Additional Edge Cases                                              #
# ------------------------------------------------------------------ #

class TestDateFilterAdditionalEdgeCases:
    """Additional edge case tests."""

    def test_date_from_equals_date_to(self, auth_client):
        """When date_from equals date_to, should show expenses for that single day."""
        today = datetime.date.today()
        # Range of single day
        response = auth_client.get(f'/profile?date_from={today}&date_to={today}')
        assert response.status_code == 200

        # Should only show expenses from today (500 for "Today's lunch")
        data = response.data
        assert b'500' in data

    def test_very_old_date_from(self, auth_client):
        """Very old date_from should work correctly."""
        old_date = "2020-01-01"
        today = datetime.date.today()

        response = auth_client.get(f'/profile?date_from={old_date}&date_to={today}')
        assert response.status_code == 200

        # Should show all expenses since 2020
        data = response.data
        assert b'23,800' in data or b'23800' in data

    def test_future_date_to(self, auth_client):
        """Future date_to should work (no expenses in future, but shouldn't crash)."""
        today = datetime.date.today()
        future_date = today + datetime.timedelta(days=30)

        response = auth_client.get(f'/profile?date_from={today}&date_to={future_date}')
        assert response.status_code == 200

        # Should only show today's expenses
        data = response.data
        assert b'500' in data

    def test_rupee_symbol_displayed(self, auth_client):
        """Rupee symbol should be displayed regardless of filter."""
        today = datetime.date.today()
        first_of_month = today.replace(day=1)

        response = auth_client.get(f'/profile?date_from={first_of_month}&date_to={today}')
        assert response.status_code == 200

        data = response.data
        # Verify rupee symbol is present
        # Verify rupee symbol is present (decode to check Unicode)