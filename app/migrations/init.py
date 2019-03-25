from app.extentions import db
from app.models.user import User, UserImage, RecoResult, Role


def migrate_up():
    print('run successful!')
    db.database.create_tables([User, UserImage, RecoResult, Role])


def rollback():
    pass
