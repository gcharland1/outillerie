from flask_login import UserMixin

from app.extensions import db

class User(UserMixin, db.Model):
    # Champs obligatoires
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False, server_default=db.text("'changeme'"))
    first_name = db.Column(db.String(250), nullable=False, server_default=db.text("'John'"))
    last_name = db.Column(db.String(250), nullable=False, server_default=db.text("'Doe'"))

    # Champs facultatifs
    adress = db.Column(db.String(250), nullable=True)
    phone = db.Column(db.String(11), nullable=True)

