from playhouse.migrate import PostgresqlMigrator, migrate
from app.extentions import db
from app.models.user import UserImage


def migrate_up():
    migrator = PostgresqlMigrator(db.database)
    migrate(migrator.add_unique(UserImage._meta.name, UserImage.file_path.name))
