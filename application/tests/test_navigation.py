import re
from datetime import timedelta
from html import unescape
from pathlib import Path

from app import loans

REFRESH_TAG = 'http-equiv="refresh"'


def page_text(response):
    return unescape(response.get_data(as_text=True))


def test_navigation_for_a_visitor(client):
    text = page_text(client.get("/login"))

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


def test_full_name_opens_the_account_menu(logged_in_client, user):
    text = page_text(logged_in_client.get("/"))

    menu = account_menu(text)
    assert '<summary><span class="account-name">Alice Tremblay</span></summary>' in menu
    assert '<a href="/tools/mine">Gérer mes outils</a>' in menu
    assert "button" not in menu


def test_account_menu_shows_upcoming_pages_greyed_out(logged_in_client):
    menu = account_menu(page_text(logged_in_client.get("/")))

    assert '<span class="menu-item-upcoming" aria-disabled="true">Préférences</span>' in menu
    assert "Mon profil" not in re.findall(r'<span class="menu-item-upcoming"[^>]*>([^<]*)<', menu)
    assert "Me déconnecter" not in menu


def test_my_profile_is_the_first_entry_of_the_account_menu(logged_in_client):
    menu = account_menu(page_text(logged_in_client.get("/")))

    items = re.search(r'<div class="account-menu-items">(.*?)</div>', menu, re.DOTALL)[1]
    assert re.search(r"<(?:a|span)\b[^>]*>([^<]*)<", items)[1] == "Mon profil"
    assert '<a href="/profile">Mon profil</a>' in menu
    assert menu.index("Mon profil") < menu.index("Gérer mes outils") < menu.index("Préférences")


def test_visitor_navigation_has_no_profile(client):
    assert "Mon profil" not in page_text(client.get("/login"))


def assert_styled_by_the_site_stylesheet(client, pages):
    for page in pages:
        html = client.get(page).get_data(as_text=True)
        assert '<link rel="stylesheet" href="/static/site.css">' in html, page
        assert "style=" not in html, page


def test_visitor_pages_use_the_site_stylesheet(client):
    assert_styled_by_the_site_stylesheet(client, ["/login", "/register", "/logged-out"])
    assert client.get("/static/site.css").status_code == 200


def test_logged_in_pages_use_the_site_stylesheet(logged_in_client):
    assert_styled_by_the_site_stylesheet(
        logged_in_client, ["/", "/tools/mine", "/tools/new", "/profile", "/profile/delete"]
    )


def test_logged_in_page_refreshes_to_expiry_page_after_lifetime(mock_app, logged_in_client):
    mock_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)

    text = page_text(logged_in_client.get("/"))

    assert '<meta http-equiv="refresh" content="905;url=/logged-out?reason=inactivity">' in text


def test_visitor_page_has_no_expiry_refresh(client):
    assert REFRESH_TAG not in page_text(client.get("/login"))


def test_logged_in_pages_are_not_cached(logged_in_client):
    assert logged_in_client.get("/").headers.get("Cache-Control") == "no-store"


def test_visitor_pages_are_cacheable(client):
    for path in ["/login", "/register"]:
        assert "no-store" not in client.get(path).headers.get("Cache-Control", ""), path


def test_account_menu_offers_my_contacts(logged_in_client):
    menu = account_menu(page_text(logged_in_client.get("/")))

    assert '<a href="/contacts">Mes contacts</a>' in menu


def test_visitor_has_neither_my_contacts_nor_search(client):
    text = page_text(client.get("/login"))

    assert "Mes contacts" not in text
    assert 'type="search"' not in text


def test_search_bar_offers_users_and_tools(logged_in_client):
    text = page_text(logged_in_client.get("/"))

    search_bar = re.search(r'<div class="nav-center">(.*?)</div>', text, re.DOTALL)[1]
    assert 'action="/search" method="get"' in search_bar
    assert '<option value="tool" selected>Outil</option>' in search_bar
    assert '<option value="user">Utilisateur</option>' in search_bar
    assert 'type="search" name="q" value=""' in search_bar
    assert 'minlength="3"' in search_bar


def test_search_bar_is_type_then_text_then_button_in_one_form(logged_in_client):
    text = page_text(logged_in_client.get("/"))

    search_bar = re.search(r'<form class="search-bar".*?</form>', text, re.DOTALL)[0]
    assert re.search(r"<select .*<input .*<button .*>Rechercher</button>", search_bar, re.DOTALL)
    assert 'placeholder="Rechercher…"' in search_bar


def test_no_page_says_voisin(client, logged_in_client):
    visitor_pages = ["/login", "/register"]
    user_pages = [
        "/",
        "/tools/mine",
        "/tools/new",
        "/contacts",
        "/loans",
        "/tools/find",
        "/search?type=user&q=bob",
        "/profile",
        "/profile/delete",
    ]

    for response in [client.get(path) for path in visitor_pages] + [
        logged_in_client.get(path) for path in user_pages
    ]:
        assert response.status_code == 200
        assert "voisin" not in page_text(response).lower()


def test_search_and_filter_are_blue(logged_in_client):
    text = page_text(logged_in_client.get("/tools/find"))

    search_bar = re.search(r'<form class="search-bar".*?</form>', text, re.DOTALL)[0]
    assert '<button type="submit" class="button primary">Rechercher</button>' in search_bar
    assert '<button type="submit" class="button primary">Filtrer</button>' in text


def test_one_blue_button_per_group(client):
    text = page_text(client.get("/login"))

    assert '<a class="button" href="/login">Connexion</a>' in text
    assert '<a class="button primary" href="/register">Inscription</a>' in text
    assert '<button type="submit" class="button primary">Se connecter</button>' in text


DESTRUCTIVE_LABELS = {
    "Retirer",
    "Confirmer le retrait",
    "Annuler le prêt",
    "Retirer ma demande",
    "Supprimer mon compte",
    "Confirmer la suppression",
}


def test_only_destructive_buttons_are_red_and_none_is_green():
    """ADR 0022: red only for a closed list of destructive buttons, never green"""
    templates = Path(__file__).parent.parent / "app" / "templates"
    colored = re.compile(r'class="button[^"]*\b(error|success)\b[^>]*>([^<{]*)<')

    offenders = [
        f"{path.name}:{number}"
        for path in templates.rglob("*.html")
        for number, line in enumerate(path.read_text().splitlines(), start=1)
        if ("error" in line or "success" in line) and 'class="button' in line
        for match in [colored.search(line)]
        if match is None or match[1] == "success" or match[2].strip() not in DESTRUCTIVE_LABELS
    ]

    assert offenders == []
    assert {button.action for button in loans.BUTTONS if button.style == "error"} == {
        "withdraw",
        "cancel",
    }
    assert "success" not in {button.style for button in loans.BUTTONS}


def test_submit_button_rule_spares_red_buttons():
    """ADR 0022: the rule that greys submit buttons keeps a red one red"""
    stylesheet = (Path(__file__).parent.parent / "app" / "static" / "site.css").read_text()

    greying = re.findall(r'\[type="submit"\]:not\(\.primary\)[^\s,{]*', stylesheet)
    assert greying == ['[type="submit"]:not(.primary):not(.error)']
