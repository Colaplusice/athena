from celery import Celery
from flask_login import LoginManager
from flask_utils.flask_env import FlaskEnv
from playhouse.flask_utils import FlaskDB

flask_env = FlaskEnv()

db = FlaskDB()

celery = Celery(__name__)

flask_login = LoginManager()
