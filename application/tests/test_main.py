from html import unescape

from flask import template_rendered


def page_text(response):
    return unescape(response.get_data(as_text=True))


def test_home_page_returns_correct_template(mock_app, logged_in_client):
    """Checks if index returns the right template"""
    captured_templates = []

    def record_template(sender, template, context, **extra):
        captured_templates.append((template, context))

    with template_rendered.connected_to(record_template, mock_app):
        response = logged_in_client.get("/")

        assert response.status_code == 200

        assert len(captured_templates) > 0

        template, context = captured_templates[0]
        assert template.name == "index.html"


def test_visitor_is_sent_to_login_without_a_message(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    assert "Veuillez vous connecter" not in page_text(client.get("/login"))


def test_back_after_logout_lands_on_login(logged_in_client):
    logged_in_client.post("/logout")

    response = logged_in_client.get("/")

    assert response.headers["Location"] == "/login"


def test_dashboard_sections_in_order(logged_in_client):
    text = page_text(logged_in_client.get("/"))

    positions = [
        text.index(title)
        for title in ("Gestion des prêts", "Gestion des contacts", "Nouveaux outils")
    ]
    assert positions == sorted(positions)
