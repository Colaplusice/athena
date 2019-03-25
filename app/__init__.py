import os

from flask import Flask
from flask_login import set_login_view
from flask_utils import update_celery

from app.extentions import flask_env, db, flask_login
from app.main.views import login, main
from app.tasks import celery
from configs import config


# load command


def create_app():
    app = Flask(__name__)
    env = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config[env])
    db.init_app(app)
    flask_env.init_app(app)
    flask_login.init_app(app)
    with app.app_context():
        set_login_view('main.login', main)
    update_celery(app, celery)
    # if env == "production":
    #     sentry.init_app(
    #         app, dsn="https://e3c5ddd746d9486d9f0a76b6953d8be2@sentry.io/1327554"
    #     )
    from .main.views import main as main_blueprint

    app.register_blueprint(main_blueprint)

    from .api import api as api_blueprint

    app.register_blueprint(api_blueprint)
    # commands
    # app.cli.add_command(usr_cli)
    return app
