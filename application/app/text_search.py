"""The matching rules every search field shares (ADR 0018)."""

from sqlalchemy import String, func, literal, select

from app.extensions import db

# \s leaves out the no-break and other Unicode spaces.
SPACES = r"[\s  -   　]+"


def normalized(expression):
    """The expression without accents, a hyphen counting as a space and runs of spaces as one"""
    if isinstance(expression, str):
        expression = literal(expression, String)
    unaccented = func.unaccent(expression, type_=String)
    spaced = func.replace(unaccented, "-", " ", type_=String)
    return func.btrim(func.regexp_replace(spaced, SPACES, " ", "g", type_=String), type_=String)


def normalize(text):
    """The searched text as the database compares it, to count its length"""
    return db.session.scalar(select(normalized(text)))


def contains(column, text):
    """Whether the column contains the text, both normalized, wildcards searched as such"""
    # Escaped after unaccent, which turns full-width ％ ＿ ＼ into the wildcards % _ \.
    escaped = normalized(text)
    for wildcard in ("\\", "%", "_"):
        escaped = func.replace(escaped, wildcard, "\\" + wildcard, type_=String)
    return normalized(column).ilike("%" + escaped + "%", escape="\\")


def sort_key(column):
    """The column as names are ordered: regardless of case and accents"""
    return func.lower(normalized(column))


def similarity(column, text):
    """How closely a word of the column resembles the text, from 0 to 1"""
    return func.word_similarity(normalized(text), normalized(column))
