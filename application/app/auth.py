from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from models.user import User

# Checked when the email is unknown, so a failed login takes the same time either way.
_DUMMY_PASSWORD_HASH = generate_password_hash("dummy-password", method="pbkdf2:sha256")

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # TODO: Valider les mdp
        email = request.form.get("email", "").strip()
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        if _account_with(email):
            flash("Le courriel est déjà utilisé")
            return render_template("sign_up.html")

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = User(
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("sign_up.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password")

        user = _account_with(email)
        password_hash = user.password if user else _DUMMY_PASSWORD_HASH

        if check_password_hash(password_hash, password) and user:
            session.permanent = True
            login_user(user)
            return redirect(url_for("index"))
        flash("Le courriel ou le mot de passe est invalide")
        return render_template("login.html", email=email)

    return render_template("login.html")


def _account_with(email):
    """The account of this email regardless of case, as the uq_user_email_lower index compares"""
    return User.query.filter(func.lower(User.email) == func.lower(email)).first()


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.logged_out"))


@bp.route("/logged-out")
def logged_out():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    minutes = int(current_app.permanent_session_lifetime.total_seconds() // 60)
    reasons = {
        "inactivity": f"Votre session a expiré après {minutes} minutes d'inactivité",
        "account-deleted": "Votre compte a été supprimé",
    }
    message = reasons.get(request.args.get("reason"), "Vous êtes déconnecté")
    return render_template("logged_out.html", message=message)
