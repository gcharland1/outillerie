"""Confirming an account's email by a signed link (ADR 0027)."""

from datetime import timedelta

from flask import current_app, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import func, select

from app import mail
from app.extensions import db
from models.user import User

LINK_LIFETIME = timedelta(days=30)
RESEND_DELAY = timedelta(minutes=5)

CONFIRMED = "Votre courriel est confirmé."
ALREADY_CONFIRMED = "Votre courriel est déjà confirmé."
EXPIRED = (
    "Ce lien a expiré. Connectez-vous pour recevoir un nouveau courriel depuis « Mon profil »."
)
INVALID = "Ce lien n'est pas valide."
SENT = "Courriel de confirmation envoyé à {email}."
TOO_SOON = (
    "Un courriel vous a été envoyé il y a moins de 5 minutes. Réessayez dans {minutes} minute(s)."
)
TO_BORROW = "Confirmez votre courriel depuis « Mon profil » pour emprunter."
TO_ACCEPT = "Confirmez votre courriel depuis « Mon profil » pour accepter une demande."


def _serializer():
    return URLSafeTimedSerializer(current_app.secret_key, salt="confirmation-courriel")


def send_link(user):
    """Emails the user a new confirmation link; the caller records when it was sent"""
    token = _serializer().dumps({"id": user.id, "email": user.email})
    # Never built from the request's Host header.
    link = current_app.config["SITE_URL"].rstrip("/") + url_for(
        "auth.confirm_email_page", token=token
    )
    days = LINK_LIFETIME.days
    body = (
        f"Bonjour {user.first_name},\n\n"
        "Confirmez votre courriel sur L'Outillerie en ouvrant ce lien :\n\n"
        f"{link}\n\n"
        f"Ce lien est valide {days} jours.\n\n"
        "Si vous n'avez pas créé de compte sur L'Outillerie, ignorez ce courriel.\n"
    )
    mail.send(mail.message(user.email, "Confirmez votre courriel", body))


def account_of(token):
    """The live account a link confirms, and the message refusing the link, if any"""
    try:
        claims = _serializer().loads(token, max_age=int(LINK_LIFETIME.total_seconds()))
    except SignatureExpired:
        return None, EXPIRED
    except BadSignature:
        return None, INVALID
    account = db.session.scalar(
        select(User).where(
            User.id == claims["id"],
            User.deleted_at.is_(None),
            func.lower(User.email) == func.lower(claims["email"]),
        )
    )
    return (account, None) if account is not None else (None, INVALID)
