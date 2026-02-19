"""
Custom decorators
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_current_user, verify_jwt_in_request


def admin_required(fn):
    """Decorator that requires admin privileges."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper





