"""Auth blueprint — registration, login, logout, profile."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, limiter
from app.models.student import Student
from app.models.user import User, UserRole
from app.utils.validators import validate_email, validate_password

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("student.onboarding"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")
        phone = request.form.get("phone", "").strip()

        errors = []
        if not validate_email(email):
            errors.append("Invalid email address.")
        if not validate_password(password):
            errors.append("Password must be at least 8 characters with one number.")
        if db.session.query(User).filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            return render_template("auth/register.html", errors=errors, name=name, email=email, role=role)

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=UserRole(role),
            phone=phone,
        )
        db.session.add(user)
        db.session.flush()

        if role == "student":
            student = Student(user_id=user.id)
            db.session.add(student)

        db.session.commit()
        login_user(user, remember=True)
        flash("Welcome to CareerGuide India! Let's set up your profile.", "success")
        return redirect(url_for("student.onboarding") if role == "student" else url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = db.session.query(User).filter_by(email=email, is_active=True).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=email)

        login_user(user, remember=remember)
        from datetime import datetime, timezone
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        next_page = request.args.get("next")
        return redirect(next_page or _redirect_by_role(user.role).location)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.phone = request.form.get("phone", current_user.phone)
        current_user.preferred_language = request.form.get("language", "en")
        db.session.commit()
        flash("Profile updated.", "success")

    return render_template("auth/profile.html", user=current_user)


def _redirect_by_role(role: UserRole):
    destinations = {
        UserRole.STUDENT: url_for("student.dashboard"),
        UserRole.PARENT: url_for("student.dashboard"),
        UserRole.COUNSELOR: url_for("admin.counselor_dashboard"),
        UserRole.ADMIN: url_for("admin.dashboard"),
    }
    return redirect(destinations.get(role, url_for("index")))
