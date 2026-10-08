"""Product service (BTH3), independent of the BTH2 authentication service."""
import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from flask import Flask, jsonify

from database import close_db
from routes import products


def create_app(test_config=None):
    load_dotenv(Path(__file__).with_name('.env'))
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.config.update(
        DB_HOST=os.getenv('DB_HOST', '127.0.0.1'),
        DB_PORT=int(os.getenv('DB_PORT', '3306')),
        DB_USER=os.getenv('DB_USER', 'root'),
        DB_PASSWORD=os.getenv('DB_PASSWORD', ''),
        DB_NAME=os.getenv('DB_NAME', 'lab03_products'),
        AUTH_URL=os.getenv('AUTH_URL', 'http://127.0.0.1:5001/auth'),
        AUTH_TIMEOUT=3, MAX_CONTENT_LENGTH=131072,
    )
    if test_config:
        app.config.update(test_config)
    app.register_blueprint(products)
    app.teardown_appcontext(close_db)

    @app.get('/')
    def home():
        return jsonify(service='Product Management - BTH3', port=5002,
                       authentication='Bearer JWT via BTH2 /auth',
                       endpoints=['GET /products', 'GET /products/<id>',
                                  'POST /products', 'PUT /products/<id>',
                                  'DELETE /products/<id>'])

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(error='NOT_FOUND'), 404

    @app.errorhandler(405)
    def wrong_method(error):
        response = jsonify(error='METHOD_NOT_ALLOWED')
        response.status_code = 405
        response.headers['Allow'] = ', '.join(error.valid_methods or [])
        return response

    @app.errorhandler(413)
    def too_large(error):
        return jsonify(error='BODY_TOO_LARGE'), 413

    @app.errorhandler(pymysql.MySQLError)
    def database_error(error):
        app.logger.error('Database operation failed (%s)', type(error).__name__)
        return jsonify(error='DATABASE_UNAVAILABLE',
                       message='Kiểm tra MySQL XAMPP và cấu hình .env'), 503

    @app.after_request
    def no_cache(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5002, debug=False)
