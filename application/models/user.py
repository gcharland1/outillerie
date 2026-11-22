from flask_login import UserMixin
from sqlalchemy import func

from app.extensions import db


class User(UserMixin, db.Model):
    # Champs obligatoires
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(250), nullable=False)
    first_name = db.Column(db.String(250), nullable=False)
    last_name = db.Column(db.String(250), nullable=False)

    # Champs facultatifs
    # NULL once the account is deleted (ADR 0023).
    email = db.Column(db.String(250), nullable=True)
    address = db.Column(db.String(250), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    email_confirmed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    email_confirmation_sent_at = db.Column(db.DateTime(timezone=True), nullable=True)

    __table_args__ = (db.Index("uq_user_email_lower", func.lower(email), unique=True),)

    @property
    def email_confirmed(self):
        return self.email_confirmed_at is not None
