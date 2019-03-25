import pendulum
from flask_login.mixins import UserMixin
from flask_utils.model import SerializerMixin
from peewee import (
    CharField,
    SmallIntegerField,
    ForeignKeyField,
    DateTimeField,
)
from playhouse.postgres_ext import JSONField

from app.extentions import db, flask_login


@flask_login.user_loader
def get_user(user_id):
    return User.get_by_id(user_id)


def verify_user(username, password):
    user = User.select().where(User.name == username, password == password).first()
    return user


class Role(db.Model):
    level = SmallIntegerField(default=1)
    name = CharField(default="user", unique=True)

    @classmethod
    def create_roles(cls):
        levels = [1, 2, 4]
        names = ["user", "admin", "me"]
        for level, name in zip(levels, names):
            cls.create(level=level, name=name)


class User(db.Model, UserMixin, SerializerMixin):
    role = ForeignKeyField(Role, Role.name, backref="user")
    name = CharField(max_length=255, unique=True)
    password = CharField(max_length=32, null=False)
    email = CharField(max_length=32, null=False)

    @classmethod
    def create_unkown(cls):
        cls.create(
            **{
                "id": 2,
                "name": "unkown",
                "password": "password",
                "email": "unkown.com",
                "role": "user",
            }
        )


class UserImage(db.Model):
    user_name = ForeignKeyField(User, User.name)
    create_at = DateTimeField(default=pendulum.now())
    file_path = CharField(null=False,unique=True)
    embedding_code = JSONField()


class RecoResult(db.Model):
    created_at = DateTimeField(default=pendulum.now())
    reco_file_path = CharField(null=False)
    result = ForeignKeyField(User, User.name)
