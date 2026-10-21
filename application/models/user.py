from flask_login import UserMixin
from sqlalchemy import func

from app.extensions import db


class User(UserMixin, db.Model):
    # Champs obligatoires
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    first_name = db.Column(db.String(250), nullable=False)
    last_name = db.Column(db.String(250), nullable=False)

    # Champs facultatifs
    address = db.Column(db.String(250), nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    __table_args__ = (db.Index("uq_user_email_lower", func.lower(email), unique=True),)
