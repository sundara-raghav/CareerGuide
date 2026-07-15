"""Input validation utilities."""

import re

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def validate_password(password: str) -> bool:
    """At least 8 chars with one digit."""
    return len(password) >= 8 and any(c.isdigit() for c in password)


def validate_phone(phone: str) -> bool:
    return bool(PHONE_RE.match(phone.replace(" ", "").replace("-", "")))


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Strip whitespace and truncate."""
    import bleach

    return bleach.clean(value.strip())[:max_length]


def validate_marks(marks: dict) -> tuple[bool, str]:
    """Validate subject marks are between 0–100."""
    for subject, score in marks.items():
        try:
            score = float(score)
        except (TypeError, ValueError):
            return False, f"Invalid marks for {subject}"
        if not 0 <= score <= 100:
            return False, f"Marks for {subject} must be between 0 and 100"
    return True, ""
