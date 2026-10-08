import pymysql
from flask import current_app, g


def connect(database=True):
    config = current_app.config
    return pymysql.connect(
        host=config['DB_HOST'], port=config['DB_PORT'], user=config['DB_USER'],
        password=config['DB_PASSWORD'],
        database=config['DB_NAME'] if database else None,
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
        autocommit=False, connect_timeout=3, read_timeout=5, write_timeout=5,
        init_command="SET time_zone = '+00:00'",
    )


def get_db():
    if 'db' not in g:
        g.db = connect()
    return g.db


def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        if error is not None:
            db.rollback()
        db.close()
