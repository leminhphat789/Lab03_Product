from flask import Blueprint

import controllers
from middleware import require_auth

products = Blueprint('products', __name__)
products.before_request(require_auth)


@products.get('/products')
def index():
    return controllers.list_products()


@products.get('/products/<int:product_id>')
def detail(product_id):
    return controllers.get_product(product_id)


@products.post('/products')
def create():
    return controllers.create_product()


@products.put('/products/<int:product_id>')
def update(product_id):
    return controllers.update_product(product_id)


@products.delete('/products/<int:product_id>')
def delete(product_id):
    return controllers.delete_product(product_id)
