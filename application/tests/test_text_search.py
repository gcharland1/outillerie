import pytest
from sqlalchemy import select

from app import text_search
from app.extensions import db


def contains(value, text):
    return db.session.scalar(select(text_search.contains(value, text)))


@pytest.mark.parametrize(
    ("value", "text"),
    [
        ("Fréd", "fred"),
        ("Fred", "FRÉD"),
        ("Jean-Pierre", "jean pierre"),
        ("Jean Pierre", "jean-pierre"),
        ("Jean–Pierre", "jean pierre"),
        ("Bob Gagnon", "bob    gagnon"),
        ("Bob Gagnon", "-bob-"),
        ("Cœur", "coeur"),
        ("O’Neil", "o'neil"),
        ("bob%%%", "％％％"),
        ("a___b", "＿＿＿"),
        ("a\\b", "＼"),
        ("50%", "50%"),
    ],
)
def test_contains(mock_app, value, text):
    with mock_app.app_context():
        assert contains(value, text)


@pytest.mark.parametrize(
    ("value", "text"),
    [
        ("abcdef", "％"),
        ("abcdef", "%"),
        ("abc", "＿"),
        ("bob", "b_b"),
        ("abc", "b＼"),
        ("Bob Gagnon", "bob gagnon x"),
    ],
)
def test_wildcards_and_strangers_do_not_match(mock_app, value, text):
    with mock_app.app_context():
        assert not contains(value, text)


@pytest.mark.parametrize(
    ("text", "result"),
    [
        ("  Fréd  Côté ", "Fred Cote"),
        ("---", ""),
        ("–––", ""),
        ("é́́", "e"),
        ("a  b", "a b"),
        ("a 　b", "a b"),
        ("Jean-Pierre", "Jean Pierre"),
    ],
)
def test_normalize(mock_app, text, result):
    with mock_app.app_context():
        assert text_search.normalize(text) == result


def test_similarity_ignores_accents(mock_app):
    with mock_app.app_context():
        score = db.session.scalar(select(text_search.similarity("Gagnon", "gagnion")))
        assert score >= 0.5
