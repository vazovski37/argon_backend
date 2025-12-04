"""
Authentication API
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt_identity,
    get_current_user
)
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.models.user import User
from app.models.progress import UserProgress
from app.extensions import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with email and password."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    name = data.get('name', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create user
    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    
    # Create initial progress
    progress = UserProgress(user_id=user.id)
    db.session.add(progress)
    db.session.commit()
    
    # Generate token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'token': access_token,
        'user': user.to_dict(),
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Find user
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 401
    
    # Generate token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'token': access_token,
        'user': user.to_dict(),
    })


@auth_bp.route('/google', methods=['POST'])
def google_auth():
    """Authenticate with Google OAuth."""
    data = request.get_json()
    credential = data.get('credential')
    
    if not credential:
        return jsonify({'error': 'No credential provided'}), 400
    
    try:
        # Verify the Google token
        client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        idinfo = id_token.verify_oauth2_token(
            credential, 
            google_requests.Request(), 
            client_id
        )
        
        google_id = idinfo['sub']
        email = idinfo.get('email', '').lower()
        name = idinfo.get('name', '')
        avatar_url = idinfo.get('picture', '')
        
        # Find existing user by Google ID or email
        user = User.query.filter(
            (User.google_id == google_id) | (User.email == email)
        ).first()
        
        if user:
            # Update Google ID if missing
            if not user.google_id:
                user.google_id = google_id
            if not user.avatar_url and avatar_url:
                user.avatar_url = avatar_url
            if not user.name and name:
                user.name = name
            db.session.commit()
        else:
            # Create new user
            user = User(
                email=email,
                google_id=google_id,
                name=name,
                avatar_url=avatar_url
            )
            db.session.add(user)
            db.session.flush()
            
            # Create initial progress
            progress = UserProgress(user_id=user.id)
            db.session.add(progress)
            db.session.commit()
        
        # Generate token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'token': access_token,
            'user': user.to_dict(),
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid Google token: {str(e)}'}), 401


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """Get current authenticated user info."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict(),
        'progress': user.progress.to_dict() if user.progress else None,
    })


@auth_bp.route('/me', methods=['PATCH'])
@jwt_required()
def update_current_user():
    """Update current user's profile."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        user.name = data['name']
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
    
    db.session.commit()
    
    return jsonify({'user': user.to_dict()})


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user's password."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'})




