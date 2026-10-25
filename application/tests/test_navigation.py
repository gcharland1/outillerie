import re
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
    assert "account-menu" not in text


def account_menu(text):
    return re.search(r'<details class="account-menu">(.*?)</details>', text, re.DOTALL)[1]


def test_navigation_for_a_logged_in_user(logged_in_client, user):
    text = page_text(logged_in_client.get("/"))

    assert 'action="/logout" method="post"' in text
    assert "Me déconnecter" in text
    assert ">Connexion<" not in text
    assert ">Inscription<" not in text


def test_username_opens_the_account_menu(logged_in_client, user):
    text = page_text(logged_in_client.get("/"))

    menu = account_menu(text)
    assert f"<summary>{user}</summary>" in menu
    assert '<a href="/tools/mine">Gérer mes outils</a>' in menu
    assert "button" not in menu


def test_account_menu_shows_upcoming_pages_greyed_out(logged_in_client):
    menu = account_menu(page_text(logged_in_client.get("/")))

    for label in ["Mon profil", "Préférences"]:
        assert f'<span class="menu-item-upcoming" aria-disabled="true">{label}</span>' in menu
    assert menu.index("Mon profil") < menu.index("Gérer mes outils") < menu.index("Préférences")
    assert "Me déconnecter" not in menu


def assert_styled_by_the_site_stylesheet(client, pages):
    for page in pages:
        html = client.get(page).get_data(as_text=True)
        assert '<link rel="stylesheet" href="/static/site.css">' in html, page
        assert "style=" not in html, page


def test_visitor_pages_use_the_site_stylesheet(client):
    assert_styled_by_the_site_stylesheet(client, ["/", "/login", "/register", "/logged-out"])
    assert client.get("/static/site.css").status_code == 200


def test_logged_in_pages_use_the_site_stylesheet(logged_in_client):
    assert_styled_by_the_site_stylesheet(logged_in_client, ["/", "/tools/mine", "/tools/new"])


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
