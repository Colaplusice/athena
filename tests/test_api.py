from app.models.user import User
from flask_utils.fake import fake_api


@fake_api(Model=User)
def test_user(client):
    pass