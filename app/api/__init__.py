"""
API Blueprints
"""
from app.api.auth import auth_bp
from app.api.game import game_bp
from app.api.locations import locations_bp
from app.api.quests import quests_bp
from app.api.photos import photos_bp
from app.api.rag import rag_bp
from app.api.groups import groups_bp

__all__ = [
    'auth_bp',
    'game_bp',
    'locations_bp',
    'quests_bp',
    'photos_bp',
    'rag_bp',
    'groups_bp',
]





