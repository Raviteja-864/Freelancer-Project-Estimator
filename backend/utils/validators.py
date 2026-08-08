import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email):
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def is_valid_password(password):
    """Password must be at least 6 chars and contain a letter and a number."""
    if not password or len(password) < 6:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


def validate_required_fields(data, required_fields):
    """Returns a list of missing field names."""
    missing = []
    if not data:
        return required_fields
    for field in required_fields:
        if field not in data or data.get(field) in (None, "", []):
            missing.append(field)
    return missing


def is_valid_role(role):
    return role in ("client", "freelancer", "admin")


def is_positive_number(value):
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def is_valid_rating(value):
    try:
        v = int(value)
        return 1 <= v <= 5
    except (TypeError, ValueError):
        return False


def is_non_negative_number(value):
    try:
        return float(value) >= 0
    except (TypeError, ValueError):
        return False


def is_positive_int(value):
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def is_valid_date(value):
    """Expects 'YYYY-MM-DD'. Returns the parsed date or None."""
    from datetime import datetime as _dt

    if not value or not isinstance(value, str):
        return None
    try:
        return _dt.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def is_valid_url(url):
    if not url or not isinstance(url, str):
        return False
    return bool(re.match(r"^https?://[^\s]+\.[^\s]+", url.strip()))


def is_valid_project_status(status):
    return status in ("open", "in_progress", "completed", "cancelled")


def is_valid_bid_status(status):
    return status in ("pending", "accepted", "rejected", "withdrawn")


def is_valid_payment_status(status):
    return status in ("pending", "paid", "cancelled")


def is_valid_account_status(status):
    return status in ("active", "suspended", "deleted")
