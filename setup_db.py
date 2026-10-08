import re
from pathlib import Path

from app import create_app
from database import connect


def initialize():
    app = create_app()
    name = app.config['DB_NAME']
    if not re.fullmatch(r'[A-Za-z0-9_]{1,64}', name):
        raise ValueError('DB_NAME must contain only letters, numbers and underscores')
    with app.app_context():
        with connect(database=False) as db:
            with db.cursor() as cursor:
                cursor.execute(f'CREATE DATABASE IF NOT EXISTS `{name}` '
                               'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))
            db.commit()
    print(f'Database {name}: products ready (existing data preserved).')


if __name__ == '__main__':
    initialize()
