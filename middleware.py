import requests
from flask import current_app, g, jsonify, request


def unauthorized(code='INVALID_TOKEN', message='JWT không hợp lệ hoặc hết hạn'):
    response = jsonify(error=code, message=message)
    response.status_code = 401
    response.headers['WWW-Authenticate'] = 'Bearer'
    return response


def require_auth():
    """Delegate JWT validation to BTH2 over HTTP; never share its DB or key."""
    parts = request.headers.get('Authorization', '').split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return unauthorized('MISSING_TOKEN', 'Cần Authorization: Bearer <JWT>')
    if len(parts[1]) > 255:
        return unauthorized()
    try:
        response = requests.get(
            current_app.config['AUTH_URL'],
            headers={'Authorization': 'Bearer ' + parts[1]},
            timeout=current_app.config['AUTH_TIMEOUT'], allow_redirects=False,
        )
        if response.status_code == 401:
            return unauthorized()
        if response.status_code != 200:
            raise ValueError('Unexpected authentication service response')
        data = response.json()
        if (not isinstance(data, dict) or data.get('authenticated') is not True
                or not isinstance(data.get('user'), dict)
                or 'IdUser' not in data['user']):
            raise ValueError('Invalid authentication service response')
        g.user = data['user']
    except (requests.RequestException, ValueError):
        return jsonify(error='AUTH_SERVICE_UNAVAILABLE',
                       message='Cần chạy service BTH2 tại cổng 5001'), 503
