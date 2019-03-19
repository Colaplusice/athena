from flask_utils.views import register_api

from app.api.views import UserView

from . import api

register_api(api, UserView, "user_api", "/user/")
