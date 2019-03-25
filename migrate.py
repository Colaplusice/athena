import pendulum
from peewee import DateTimeField, CharField, AutoField

from app.extentions import db


class MigrateRecord(db.Model):
    created_at = DateTimeField(default=pendulum.now())
    name = CharField(null=False)
    migrate_id = AutoField()


import os

from werkzeug.utils import import_string


def run():
    if not db.database.table_exists('migraterecord'):
        db.database.create_tables([MigrateRecord])

    package_name = 'app/migrations'
    file_list = os.listdir(package_name)
    migration_list = []
    for file in file_list:
        if not file.endswith('.py') or file == '__init__.py':
            continue
        print(file)
        import_name = package_name.replace('/', '.') + '.' + file[:-3] + ':migrate_up'
        print(import_name)
        function = import_string(import_name)
        migration_list.append((file[:-3], function))
    migrate_records = {record.name for record in MigrateRecord.select()}
    for migrate in migration_list:
        if migrate[0] not in migrate_records:
            migrate[1]()
            MigrateRecord.create(**{'name': migrate[0]})


def destroy():
    pass
    # db.database.