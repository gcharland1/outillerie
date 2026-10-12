import pytest 

from flask import template_rendered
from app import create_app

@pytest.fixture
def mock_app():
    """Create an app instance for testing"""
    app = create_app()
    app.config.update({
                      "TESTING": True,
    })
    yield app

@pytest.fixture 
def client(mock_app):
    """An app client to send requests"""
    return mock_app.test_client()

def test_home_page_returns_correct_template(mock_app, client):
    """Checks if index returns the right template"""
    captured_templates = []

    def record_template(sender, template, context, **extra):
        captured_templates.append((template, context))

    with template_rendered.connected_to(record_template, mock_app):
        response = client.get('/')

        assert response.status_code == 200

        assert len(captured_templates) > 0

        template, context = captured_templates[0]
        assert template.name == 'index.html'


