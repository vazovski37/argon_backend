"""
Flask Extensions
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


# JWT callbacks
@jwt.user_identity_loader
def user_identity_lookup(user):
    """Convert user to identity for JWT."""
    return str(user)


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Load user from JWT identity."""
    from app.models.user import User
    identity = jwt_data["sub"]
    return User.query.get(identity)





