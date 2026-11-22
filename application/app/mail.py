"""Sending emails over SMTP; in tests, kept in memory; in development, logged (ADR 0027)."""

import logging
import re
import smtplib
from email.message import EmailMessage

from flask import current_app

SMTP_SSL_PORT = 465
SMTP_TIMEOUT_SECONDS = 10


def message(to, subject, body):
    """An email from the configured sender"""
    email = EmailMessage()
    email["From"] = current_app.config["MAIL_SENDER"]
    email["To"] = to
    email["Subject"] = subject
    email.set_content(body)
    return email


def send(email):
    """Sends the email; a failure is logged without its content and never raised"""
    config = current_app.config
    if config.get("TESTING"):
        current_app.extensions.setdefault("mail_outbox", []).append(email)
        return
    if not config.get("SMTP_HOST"):
        current_app.logger.info("Courriel non envoyé, SMTP non configuré :\n%s", email)
        return
    try:
        with _connection(config) as smtp:
            smtp.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
            smtp.send_message(email)
    except (smtplib.SMTPException, OSError) as error:
        current_app.logger.error("Échec de l'envoi d'un courriel : %s", type(error).__name__)


def _connection(config):
    host, port = config["SMTP_HOST"], config["SMTP_PORT"]
    if port == SMTP_SSL_PORT:
        return smtplib.SMTP_SSL(host, port, timeout=SMTP_TIMEOUT_SECONDS)
    smtp = smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT_SECONDS)
    try:
        smtp.starttls()
    except BaseException:
        smtp.close()
        raise
    return smtp


class ConfirmationTokenFilter(logging.Filter):
    """Masks the token of a confirmation link in the request lines Werkzeug logs"""

    TOKEN = re.compile(r"(/confirmer-courriel/)[^\s?\"]+")

    def filter(self, record):
        masked = self.TOKEN.sub(r"\1…", record.getMessage())
        record.msg, record.args = masked, ()
        return True


def mask_confirmation_tokens():
    logger = logging.getLogger("werkzeug")
    if not any(isinstance(f, ConfirmationTokenFilter) for f in logger.filters):
        logger.addFilter(ConfirmationTokenFilter())
