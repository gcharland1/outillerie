"""Sending emails over SMTP; in tests, kept in memory; in development, logged (ADR 0027)."""

import logging
import re
import smtplib
from email.message import EmailMessage
from email.utils import getaddresses

from flask import current_app

SMTP_SSL_PORT = 465
SMTP_TIMEOUT_SECONDS = 10


def send(to, subject, body):
    """Sends an email to one address; a failure is logged without its content and never raised"""
    config = current_app.config
    try:
        email = _message(to, subject, body)
        if config.get("TESTING"):
            current_app.extensions.setdefault("mail_outbox", []).append(email)
            return
        if not config.get("SMTP_HOST"):
            # Above the default WARNING level, so the link shows in the development log.
            current_app.logger.warning("Courriel non envoyé, SMTP non configuré :\n%s", email)
            return
        with _connection(config) as smtp:
            smtp.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
            smtp.send_message(email, to_addrs=[to])
    except Exception as error:  # noqa: BLE001 - a failed send never fails the caller
        current_app.logger.error("Échec de l'envoi d'un courriel : %s", type(error).__name__)


def _message(to, subject, body):
    # A typed "a@x, b@y" would otherwise send the account's link to a second person.
    if [address for _, address in getaddresses([to])] != [to]:
        raise ValueError("not a single email address")
    email = EmailMessage()
    email["From"] = current_app.config["MAIL_SENDER"]
    email["To"] = to
    email["Subject"] = subject
    email.set_content(body)
    return email


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
