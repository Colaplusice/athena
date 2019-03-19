from flask_utils.fake import fake_api

from app.models.user import User


@fake_api(Model=User)
def test_user(client):
    pass
