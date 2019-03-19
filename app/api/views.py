from flask_utils.restframework import ModelViewSet

from app.models.user import User


class UserView(ModelViewSet):
    model_class = User


