from datetime import timedelta
from html import unescape

REFRESH_TAG = 'http-equiv="refresh"'


def page_text(response):
    return unescape(response.get_data(as_text=True))


def test_navigation_for_a_visitor(client):
    text = page_text(client.get("/"))

    assert "Connexion" in text
    assert "Inscription" in text
    assert "Me déconnecter" not in text
    assert "Gérer mes outils" not in text


def test_navigation_for_a_logged_in_user(logged_in_client, user):
    text = page_text(logged_in_client.get("/"))

    assert f">{user}</span>" in text
    assert 'action="/logout" method="post"' in text
    assert "Me déconnecter" in text
    assert '<a href="/tools/mine">Gérer mes outils</a>' in text
    assert ">Connexion<" not in text
    assert ">Inscription<" not in text


def test_logged_in_page_refreshes_to_expiry_page_after_lifetime(mock_app, logged_in_client):
    mock_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)

    text = page_text(logged_in_client.get("/"))

    assert '<meta http-equiv="refresh" content="905;url=/logged-out?reason=inactivity">' in text


def test_visitor_page_has_no_expiry_refresh(client):
    assert REFRESH_TAG not in page_text(client.get("/"))


def test_logged_in_pages_are_not_cached(logged_in_client):
    assert logged_in_client.get("/").headers.get("Cache-Control") == "no-store"


def test_visitor_pages_are_cacheable(client):
    assert "no-store" not in client.get("/").headers.get("Cache-Control", "")
