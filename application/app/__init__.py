import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

from app.extensions import csrf, db, login_manager, migrate


def create_app(test_config=None):
    """Creates an app and sets it's routes, using test_config instead of the environment if given"""

    app = _initialize_app(test_config)
    # Trust only the scheme set by the single proxy in front of the app (ADR 0015).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=0, x_proto=1)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import auth, contacts, search, tools
    from models.user import User

    app.register_blueprint(auth.bp)
    app.register_blueprint(tools.bp)
    app.register_blueprint(contacts.bp)
    app.register_blueprint(search.bp)

    @app.route("/")
    def index():
        username = None
        if current_user.is_authenticated:
            username = current_user.username
        return render_template("index.html", username=username)

    @app.after_request
    def prevent_caching_for_logged_in_user(response):
        # The photo sets its own private cache (ADR 0014).
        if current_user.is_authenticated and request.endpoint != "tools.photo":
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(CSRFError)
    def refuse_form_without_valid_token(error):
        return render_template("csrf_error.html"), 400

    @app.errorhandler(RequestEntityTooLarge)
    def refuse_too_large_request(error):
        return render_template("too_large.html"), 413

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return app


def _initialize_app(test_config):
    """Initializes and configures the app reading from .env file, or from test_config if given"""
    environment = os.getenv("FLASK_ENVIRONMENT", "development")
    app = Flask(__name__)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Behind Cloudflare Tunnel, the browser only ever talks HTTPS (ADR 0015).
    app.config["SESSION_COOKIE_SECURE"] = environment != "development"
    # The token lives as long as the session that holds it (ADR 0012).
    app.config["WTF_CSRF_TIME_LIMIT"] = None
    # Safety cap on any request; the photo's own 10 MB limit is checked by the view (ADR 0014).
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    if test_config is not None:
        app.config.from_mapping(test_config)
        return app

    if environment == "development":
        load_dotenv()

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

    return app
