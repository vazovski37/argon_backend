"""
Achievement Models
"""
from datetime import datetime
from uuid import uuid4
from app.extensions import db


class Achievement(db.Model):
    """Achievements that users can earn."""
    
    __tablename__ = 'achievements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(10), default='🏆')  # Emoji icon
    
    # XP reward for earning this achievement
    xp_reward = db.Column(db.Integer, default=100)
    
    # Requirement type: visits, photos, quests, phrases, special
    requirement_type = db.Column(db.String(50), nullable=True)
    requirement_value = db.Column(db.Integer, nullable=True)
    
    # Hidden achievements
    is_secret = db.Column(db.Boolean, default=False)
    
    # Category for grouping
    category = db.Column(db.String(50), default='general')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_achievements = db.relationship('UserAchievement', backref='achievement', cascade='all, delete-orphan')
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'xp_reward': self.xp_reward,
            'requirement_type': self.requirement_type,
            'requirement_value': self.requirement_value,
            'is_secret': self.is_secret,
            'category': self.category,
        }
    
    def __repr__(self):
        return f'<Achievement {self.name}>'


class UserAchievement(db.Model):
    """Track which achievements users have earned."""
    
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    achievement_id = db.Column(db.String(36), db.ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False)
    
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: user can only earn each achievement once
    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'achievement': self.achievement.to_dict() if self.achievement else None,
        }
    
    def __repr__(self):
        return f'<UserAchievement {self.user_id} -> {self.achievement_id}>'




