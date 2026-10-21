import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager, migrate

# Checked when the username is unknown, so a failed login takes the same time either way.
_DUMMY_PASSWORD_HASH = generate_password_hash("dummy-password", method="pbkdf2:sha256")


def create_app(test_config=None):
    """Creates an app and sets it's routes, using test_config instead of the environment if given"""

    app = _initialize_app(test_config)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from models.user import User

    @app.route("/")
    def index():
        username = None
        if current_user.is_authenticated:
            username = current_user.username
        return render_template("index.html", username=username)

    @app.route("/register", methods=["GET", "POST"])
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

            return redirect(url_for("login"))

        return render_template("sign_up.html")

    @app.route("/login", methods=["GET", "POST"])
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

    @app.route("/logout", methods=["POST"])
    def logout():
        logout_user()
        session.clear()
        return redirect(url_for("logged_out"))

    @app.route("/logged-out")
    def logged_out():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        expired = request.args.get("reason") == "inactivity"
        minutes = int(app.permanent_session_lifetime.total_seconds() // 60)
        return render_template("logged_out.html", expired=expired, minutes=minutes)

    @app.after_request
    def prevent_caching_for_logged_in_user(response):
        if current_user.is_authenticated:
            response.headers["Cache-Control"] = "no-store"
        return response

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app


def _initialize_app(test_config):
    """Initializes and configures the app reading from .env file, or from test_config if given"""
    app = Flask(__name__)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    if test_config is not None:
        app.config.from_mapping(test_config)
        return app

    if os.getenv("FLASK_ENVIRONMENT", "development") == "development":
        load_dotenv()

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

    return app
