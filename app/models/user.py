from flask_utils.model import SerializerMixin
from peewee import CharField
from app.extentions import db

class User(db.Model, SerializerMixin):
    name = CharField(max_length=255)
    password = CharField(max_length=32, null=False)
