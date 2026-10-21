from datetime import date

from app.extensions import db
from models import Tool, User


def a_day(day):
    """A day of November 2026, the month the specs' scenarios use"""
    return date(2026, 11, day)


def make_tool(owner_id, name="Perceuse", description="Perceuse sans fil"):
    tool = Tool(owner_id=owner_id, name=name, description=description)
    db.session.add(tool)
    db.session.commit()
    return tool


def make_user(username, email, **fields):
    """An unsaved account whose password value is not a real hash"""
    return User(
        username=username,
        password="hash",
        first_name="Prénom",
        last_name="Nom",
        email=email,
        **fields,
    )
