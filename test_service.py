import unittest
from decimal import Decimal
from unittest.mock import Mock, patch

import requests
from app import create_app
from controllers import validate_product


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()

    def validate(self, data):
        with self.app.test_request_context('/products', method='POST', json=data):
            return validate_product()

    def test_valid_decimal_and_unicode(self):
        values = self.validate(dict(name='  Bàn phím  ', description='Tiếng Việt',
                                    price='12345678.90', quantity=10))
        self.assertEqual(values, ('Bàn phím', 'Tiếng Việt', Decimal('12345678.90'), 10))

    def test_reject_invalid_money(self):
        for price in ['NaN', 'Infinity', '-1', '100000000.00', '1.001', True, [], 'abc']:
            with self.subTest(price=price), self.assertRaises(ValueError):
                self.validate(dict(name='Demo', description='', price=price, quantity=0))

    def test_reject_invalid_quantity(self):
        for quantity in [-1, 1.5, True, '1', 2147483648, None]:
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                self.validate(dict(name='Demo', description='', price='0.00', quantity=quantity))

    def test_reject_invalid_names(self):
        for name in ['', ' ', 'x'*256, None, 15]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.validate(dict(name=name, description='', price='0.00', quantity=0))

    def test_reject_unknown_or_missing_fields(self):
        for data in [{}, [], {'id': 1},
                     dict(name='Demo', description='', price='1.00', quantity=1, id=1)]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.validate(data)

    def test_all_routes_require_auth(self):
        for method, path in [('GET', '/products'), ('GET', '/products/1'),
                             ('POST', '/products'), ('PUT', '/products/1'),
                             ('DELETE', '/products/1')]:
            with self.subTest(method=method):
                response = self.client.open(path, method=method)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json['error'], 'MISSING_TOKEN')

    @patch('middleware.requests.get')
    def test_remote_rejects_token(self, remote):
        remote.return_value = Mock(status_code=401)
        response = self.client.get('/products', headers={'Authorization': 'Bearer a.b.c'})
        self.assertEqual(response.status_code, 401)
        self.assertFalse(remote.call_args.kwargs['allow_redirects'])

    @patch('middleware.requests.get')
    def test_auth_timeout_fails_closed(self, remote):
        remote.side_effect = requests.Timeout()
        response = self.client.get('/products', headers={'Authorization': 'Bearer a.b.c'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json['error'], 'AUTH_SERVICE_UNAVAILABLE')

    @patch('middleware.requests.get')
    def test_invalid_auth_response_fails_closed(self, remote):
        for status, body in [(500, {}), (302, {}), (200, []),
                             (200, {'authenticated': False}),
                             (200, {'authenticated': True, 'user': {}})]:
            with self.subTest(status=status, body=body):
                remote.return_value = Mock(status_code=status, json=Mock(return_value=body))
                self.assertEqual(self.client.get('/products', headers={
                    'Authorization': 'Bearer a.b.c'}).status_code, 503)

    def test_money_numeric_json_is_exact(self):
        with self.app.test_request_context('/products', method='POST',
                data='{"name":"Demo","description":"","price":12.30,"quantity":0}',
                content_type='application/json'):
            self.assertEqual(validate_product()[2], Decimal('12.30'))

    def test_text_body_and_nan_rejected(self):
        for content_type, body in [('text/plain', '{}'), ('application/json',
                '{"name":"Demo","description":"","price":NaN,"quantity":0}')]:
            with self.subTest(content_type=content_type), self.app.test_request_context(
                '/products', method='POST', data=body, content_type=content_type):
                with self.assertRaises(ValueError):
                    validate_product()

    def test_public_service_information(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/').json['port'], 5002)


if __name__ == '__main__':
    unittest.main(verbosity=2)
