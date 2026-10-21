from flask import template_rendered


def test_home_page_returns_correct_template(mock_app, client):
    """Checks if index returns the right template"""
    captured_templates = []

    def record_template(sender, template, context, **extra):
        captured_templates.append((template, context))

    with template_rendered.connected_to(record_template, mock_app):
        response = client.get("/")

        assert response.status_code == 200

        assert len(captured_templates) > 0

        template, context = captured_templates[0]
        assert template.name == "index.html"
