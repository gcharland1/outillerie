from datetime import date

from app.extensions import db
from models import ContactRelation, ContactRequest, Tool, User


def a_day(day):
    """A day of November 2026, the month the specs' scenarios use"""
    return date(2026, 11, day)


def make_tool(owner_id, name="Perceuse", description="Perceuse sans fil", **fields):
    tool = Tool(owner_id=owner_id, name=name, description=description, **fields)
    db.session.add(tool)
    db.session.commit()
    return tool


def make_user(username, email, **fields):
    """An unsaved account whose password value is not a real hash"""
    fields = {"first_name": "Prénom", "last_name": "Nom", **fields}
    return User(username=username, password="hash", email=email, **fields)


def make_contact_request(requester_id, recipient_id):
    request = ContactRequest(requester_id=requester_id, recipient_id=recipient_id)
    db.session.add(request)
    db.session.commit()
    return request


def make_contact_relation(first_id, second_id):
    relation = ContactRelation.between(first_id, second_id)
    db.session.add(relation)
    db.session.commit()
    return relation


def user_id(username):
    return User.query.filter_by(username=username).one().id
