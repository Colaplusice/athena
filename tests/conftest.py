import os

import pytest

from app import create_app


def pytest_sessionstart(session):
    os.environ["FLASK_ENV"] = "testing"
    create_app()


@pytest.fixture(scope="session")
def app():
    os.environ["FLASK_ENV"] = "testing"
    app = create_app()
    # 必须在create_app后 model user才能用。。
    from app.models.user import User

    with app.app_context():
        app.database.create_tables([User])
        yield app
        app.database.drop_tables([User])


@pytest.fixture
def client(app):
    client = app.test_client()
    return client
