"""
Quest Models
"""
from datetime import datetime
from uuid import uuid4
from app.extensions import db


class Quest(db.Model):
    """Quests that users can undertake."""
    
    __tablename__ = 'quests'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    story_intro = db.Column(db.Text, nullable=True)  # Narrative introduction
    
    # XP reward for completing the quest
    xp_reward = db.Column(db.Integer, default=200)
    
    # Quest steps as JSON array: [{title, description, location_id}]
    steps = db.Column(db.JSON, nullable=False, default=list)
    
    # Quest type
    is_daily = db.Column(db.Boolean, default=False)
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    
    # Estimated time in minutes
    estimated_time = db.Column(db.Integer, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_quests = db.relationship('UserQuest', backref='quest', cascade='all, delete-orphan')
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'story_intro': self.story_intro,
            'xp_reward': self.xp_reward,
            'steps': self.steps or [],
            'is_daily': self.is_daily,
            'difficulty': self.difficulty,
            'estimated_time': self.estimated_time,
            'step_count': len(self.steps) if self.steps else 0,
        }
    
    def __repr__(self):
        return f'<Quest {self.name}>'


class UserQuest(db.Model):
    """Track user quest progress."""
    
    __tablename__ = 'user_quests'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    quest_id = db.Column(db.String(36), db.ForeignKey('quests.id', ondelete='CASCADE'), nullable=False)
    
    # Status: active, completed, abandoned
    status = db.Column(db.String(20), default='active')
    
    # Current step (0-indexed)
    current_step = db.Column(db.Integer, default=0)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Unique constraint: user can only have one instance of each quest
    __table_args__ = (
        db.UniqueConstraint('user_id', 'quest_id', name='unique_user_quest'),
    )
    
    def advance_step(self) -> bool:
        """Advance to the next step. Returns True if quest completed."""
        if self.quest and self.quest.steps:
            total_steps = len(self.quest.steps)
            self.current_step += 1
            
            if self.current_step >= total_steps:
                self.status = 'completed'
                self.completed_at = datetime.utcnow()
                return True
        return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'quest_id': self.quest_id,
            'status': self.status,
            'current_step': self.current_step,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'quest': self.quest.to_dict() if self.quest else None,
        }
    
    def __repr__(self):
        return f'<UserQuest {self.user_id} -> {self.quest_id} ({self.status})>'




