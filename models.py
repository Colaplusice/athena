from base64 import b64decode, b64encode

import pendulum
from flask_utils.model import SerializerMixin
from peewee import *
from playhouse.postgres_ext import JSONField
from playhouse.postgres_ext import PostgresqlExtDatabase

database = PostgresqlExtDatabase(
    database="athena", user="fjl2401", host="127.0.0.1", port="5432",
    autocommit=True, autorollback=True
)


def decode_user(_id):
    message = b64decode(_id).decode('utf-8').split("-")
    return message[0], message[1]


def encode_user(username, password):
    res = "-".join([username, password]).encode("utf-8")
    return b64encode(res)


class Role(Model):
    class Meta:
        database = database

    level = SmallIntegerField(default=1)
    name = CharField(default="user", unique=True)

    @classmethod
    def create_roles(cls):
        levels = [1, 2, 4]
        names = ["user", "admin", "me"]
        for level, name in zip(levels, names):
            cls.get_or_create(level=level, name=name)


class User(Model, SerializerMixin):
    class Meta:
        database = database

    role = ForeignKeyField(Role, Role.name, backref="user", default="user")
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

    @classmethod
    def get_user(cls, id):
        username, password = decode_user(id.encode('utf-8'))
        user = (
            cls.select().where(cls.name == username, cls.password == password).first()
        )
        return user


class UserImage(Model):
    class Meta:
        database = database

    user_name = ForeignKeyField(User, User.name)
    create_at = DateTimeField(default=pendulum.now())
    file_path = CharField(null=False, unique=True)
    embedding_code = JSONField()

    def __repr__(self):
        return self.user_name


# 和user关联。属于个性化范围的Model 比如年龄检测
class RecoResult(Model):
    class Meta:
        database = database

    created_at = DateTimeField(default=pendulum.now())
    reco_file_path = CharField(null=False)
    result = ForeignKeyField(User, User.name)


#
with database.transaction():
    database.create_tables([User, Role, RecoResult, UserImage])
    Role.create_roles()
