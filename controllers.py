import json
from decimal import Decimal, InvalidOperation

from flask import jsonify, request, url_for

from database import get_db

FIELDS = {'name', 'description', 'price', 'quantity'}


def reject_constant(value):
    raise ValueError('Non-finite number')


def validate_product():
    if not request.is_json:
        raise ValueError('Body phải là JSON; dùng Content-Type: application/json')
    try:
        data = json.loads(request.get_data(as_text=True), parse_float=Decimal,
                          parse_constant=reject_constant)
    except (ValueError, UnicodeDecodeError):
        raise ValueError('Body phải là JSON hợp lệ') from None
    if not isinstance(data, dict) or set(data) != FIELDS:
        raise ValueError('Cần đúng 4 trường: name, description, price, quantity')
    name, description = data['name'], data['description']
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 255:
        raise ValueError('name phải có từ 1 đến 255 ký tự')
    if not isinstance(description, str) or len(description.encode('utf-8')) > 65535:
        raise ValueError('description phải là chuỗi, tối đa 65535 byte UTF-8')
    if isinstance(data['price'], bool) or not isinstance(data['price'], (str, int, Decimal)):
        raise ValueError('price phải là số hoặc chuỗi thập phân')
    try:
        price = Decimal(data['price'])
        if (not price.is_finite() or price < 0 or price > Decimal('99999999.99')
                or price != price.quantize(Decimal('0.01'))):
            raise ValueError('price phải từ 0 đến 99999999.99, tối đa 2 chữ số lẻ')
    except (InvalidOperation, ValueError, OverflowError):
        raise ValueError('price phải từ 0 đến 99999999.99, tối đa 2 chữ số lẻ') from None
    quantity = data['quantity']
    if type(quantity) is not int or not 0 <= quantity <= 2147483647:
        raise ValueError('quantity phải là số nguyên từ 0 đến 2147483647')
    return name.strip(), description, price.quantize(Decimal('0.01')), quantity


def serialize(row):
    return dict(id=row['id'], name=row['name'], description=row['description'],
                price=format(row['price'], '.2f'), quantity=row['quantity'],
                created_at=row['created_at'].isoformat() + 'Z',
                updated_at=row['updated_at'].isoformat() + 'Z')


def missing():
    return jsonify(error='PRODUCT_NOT_FOUND'), 404


def list_products():
    with get_db().cursor() as cursor:
        cursor.execute('SELECT * FROM products ORDER BY id')
        return jsonify([serialize(row) for row in cursor.fetchall()])


def get_product(product_id):
    with get_db().cursor() as cursor:
        cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        row = cursor.fetchone()
        return jsonify(serialize(row)) if row else missing()


def create_product():
    try:
        values = validate_product()
    except ValueError as error:
        return jsonify(error='INVALID_INPUT', message=str(error)), 400
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('INSERT INTO products (name, description, price, quantity) '
                       'VALUES (%s, %s, %s, %s)', values)
        product_id = cursor.lastrowid
        cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        product = serialize(cursor.fetchone())
    db.commit()
    response = jsonify(product)
    response.status_code = 201
    response.headers['Location'] = url_for('products.detail', product_id=product_id)
    return response


def update_product(product_id):
    try:
        values = validate_product()
    except ValueError as error:
        return jsonify(error='INVALID_INPUT', message=str(error)), 400
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('SELECT id FROM products WHERE id = %s FOR UPDATE', (product_id,))
        if cursor.fetchone() is None:
            db.rollback()
            return missing()
        cursor.execute('UPDATE products SET name=%s, description=%s, price=%s, '
                       'quantity=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s',
                       (*values, product_id))
        cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        product = serialize(cursor.fetchone())
    db.commit()
    return jsonify(product)


def delete_product(product_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
        affected = cursor.rowcount
    db.commit()
    return ('', 204) if affected else missing()
