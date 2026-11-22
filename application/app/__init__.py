import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

from app import mail
from app.extensions import csrf, db, login_manager, migrate

# The value .env.example ships with.
EXAMPLE_SECRET_KEY = "dev-seulement"
MAIL_VARIABLES = (
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "MAIL_SENDER",
    "SITE_URL",
)
DEVELOPMENT_MAIL_DEFAULTS = {
    "SMTP_PORT": "587",
    "MAIL_SENDER": "outillerie@localhost",
    "SITE_URL": "http://localhost:5000",
}


def create_app(test_config=None):
    """Creates an app and sets it's routes, using test_config instead of the environment if given"""

    app = _initialize_app(test_config)
    mail.mask_confirmation_tokens()
    # Trust only the scheme set by the single proxy in front of the app (ADR 0015).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=0, x_proto=1)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import auth, catalog, contacts, loans, profile, search, tools
    from models.user import User

    app.register_blueprint(auth.bp)
    app.register_blueprint(tools.bp)
    app.register_blueprint(contacts.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(loans.bp)
    app.register_blueprint(profile.bp)

    @app.route("/")
    def index():
        # Not login_required: arriving on the site is no reason for its "please log in" message.
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        since = catalog.recent_since()
        new_tools, more_tools = catalog.recent_tools(current_user.id, since)
        return render_template(
            "index.html",
            loan_groups=loans.dashboard(current_user.id),
            contact_requests=contacts.received_requests(current_user.id),
            new_contacts=contacts.recent_contacts(current_user.id, since),
            new_tools=new_tools,
            more_tools=more_tools,
            has_contacts=catalog.has_contacts(current_user.id),
            no_new_tool=catalog.NO_NEW_TOOL,
            no_contact=catalog.NO_CONTACT,
        )

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
        # None makes it a visitor's session: a deleted account's end everywhere (ADR 0023).
        user = db.session.get(User, int(user_id))
        return user if user is not None and user.deleted_at is None else None

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
    app.config["SECRET_KEY"] = _secret_key(environment)
    app.config.update(_mail_settings(environment))

    return app


def _secret_key(environment):
    """Returns FLASK_SECRET_KEY, refusing outside development a missing, empty or example key"""
    if environment == "development":
        return os.environ["FLASK_SECRET_KEY"]
    key = os.getenv("FLASK_SECRET_KEY", "")
    if key in ("", EXAMPLE_SECRET_KEY):
        raise RuntimeError(f"FLASK_SECRET_KEY must hold a real secret in {environment}")
    return key


def _mail_settings(environment):
    """The SMTP settings, refusing outside development a missing or empty one (ADR 0027)"""
    settings = {name: os.getenv(name, "").strip() for name in MAIL_VARIABLES}
    for name, value in settings.items():
        if value:
            continue
        if environment != "development":
            raise RuntimeError(f"{name} must be set in {environment}")
        settings[name] = DEVELOPMENT_MAIL_DEFAULTS.get(name)
    if not settings["SMTP_PORT"].isdigit():
        raise RuntimeError("SMTP_PORT must be a port number")
    settings["SMTP_PORT"] = int(settings["SMTP_PORT"])
    return settings
