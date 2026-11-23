from flask import (
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_remembered, login_user, logout_user
from flask_login.signals import user_loaded_from_cookie
from sqlalchemy import func, update
from werkzeug.security import check_password_hash, generate_password_hash

from app import email_confirmation
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
            email_confirmation_sent_at=func.now(),
        )

        db.session.add(new_user)
        db.session.commit()
        email_confirmation.send_link(new_user)

        flash(f"Compte créé. Un courriel de confirmation a été envoyé à {email}.", "success")
        return redirect(url_for("auth.login"))

    return render_template("sign_up.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password")
        remember = request.form.get("remember") == "1"

        user = _account_with(email)
        password_hash = user.password if user else _DUMMY_PASSWORD_HASH

        if check_password_hash(password_hash, password) and user:
            session.permanent = True
            login_user(user, remember=remember)
            if not remember:
                # login_user leaves the remember cookie of an earlier login in place.
                session["_remember"] = "clear"
            return redirect(url_for("index"))
        flash("Le courriel ou le mot de passe est invalide")
        return render_template("login.html", email=email, remember=remember)

    return render_template("login.html")


def _account_with(email):
    """The account of this email regardless of case, as the uq_user_email_lower index compares"""
    return User.query.filter(func.lower(User.email) == func.lower(email)).first()


@bp.route("/confirmer-courriel/<token>")
def confirm_email_page(token):
    account, error = email_confirmation.account_of(token)
    return _render_confirm_email(token if account else None, error)


@bp.route("/confirmer-courriel", methods=["POST"])
def confirm_email():
    # The link's account, never the session's; confirming opens no session.
    account, error = email_confirmation.account_of(request.form.get("token", ""))
    if account is None:
        return _render_confirm_email(None, error)
    db.session.execute(
        update(User)
        .where(
            User.id == account.id,
            func.lower(User.email) == func.lower(account.email),
            User.deleted_at.is_(None),
            User.email_confirmed_at.is_(None),
        )
        .values(email_confirmed_at=func.now())
        .execution_options(synchronize_session=False)
    )
    db.session.commit()
    flash(email_confirmation.CONFIRMED, "success")
    if current_user.is_authenticated:
        return redirect(url_for("profile.show"))
    return redirect(url_for("auth.login"))


def _render_confirm_email(token, error):
    response = make_response(render_template("confirm_email.html", token=token, error=error))
    # The link holds the token: no other site may receive it. Not no-referrer: over HTTPS,
    # Flask-WTF refuses the button's POST without a same-origin Referer.
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@bp.route("/logout", methods=["POST"])
def logout():
    end_session()
    return redirect(url_for("auth.logged_out"))


def end_session():
    """Ends the session and erases the remember cookie of this device"""
    # Cleared first: logout_user marks the remember cookie for erasure in the session.
    session.clear()
    logout_user()


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


@bp.after_app_request
def keep_remember_cookie_in_step(response):
    """Renews the remember cookie of a recognized user for 30 days, erases one the loader refused"""
    # Runs before Flask-Login's own after_request, which sets or erases the cookie.
    if "_remember" not in session and login_remembered():
        session["_remember"] = "set" if current_user.is_authenticated else "clear"
    return response


@user_loaded_from_cookie.connect
def make_restored_session_permanent(app, user):
    session.permanent = True


@bp.app_context_processor
def inject_expires_on_inactivity():
    """Whether the page sends the browser to the expiry notice after 30 minutes"""
    return {"expires_on_inactivity": current_user.is_authenticated and not login_remembered()}
