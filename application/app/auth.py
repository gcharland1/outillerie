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

# Checked when the username is unknown, so a failed login takes the same time either way.
_DUMMY_PASSWORD_HASH = generate_password_hash("dummy-password", method="pbkdf2:sha256")

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # TODO: Valider les mdp
        username = request.form.get("username")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")

        if User.query.filter_by(username=username).first():
            flash("Le nom d'utilisateur est déjà utilisé")
            return render_template("sign_up.html")

        if User.query.filter(func.lower(User.email) == func.lower(email)).first():
            flash("Le courriel est déjà utilisé")
            return render_template("sign_up.html")

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = User(
            username=username,
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
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        password_hash = user.password if user else _DUMMY_PASSWORD_HASH

        if check_password_hash(password_hash, password) and user:
            session.permanent = True
            login_user(user)
            return redirect(url_for("index"))
        flash("Le nom d'utilisateur ou le mot de passe est invalide")

    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.logged_out"))


@bp.route("/logged-out")
def logged_out():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    expired = request.args.get("reason") == "inactivity"
    minutes = int(current_app.permanent_session_lifetime.total_seconds() // 60)
    return render_template("logged_out.html", expired=expired, minutes=minutes)
