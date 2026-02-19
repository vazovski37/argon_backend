"""
User Progress Model - Game State
"""
from datetime import datetime
from uuid import uuid4
from app.extensions import db


# XP thresholds for each level
LEVEL_THRESHOLDS = [
    0,      # Level 1
    100,    # Level 2
    250,    # Level 3
    500,    # Level 4
    1000,   # Level 5
    1750,   # Level 6
    2750,   # Level 7
    4000,   # Level 8
    5500,   # Level 9
    7500,   # Level 10
]

# Ranks based on level
RANKS = {
    1: 'Tourist',
    2: 'Visitor',
    3: 'Explorer',
    4: 'Adventurer',
    5: 'Discoverer',
    6: 'Pathfinder',
    7: 'Wayfarer',
    8: 'Navigator',
    9: 'Argonaut',
    10: 'Legend of Colchis',
}


class UserProgress(db.Model):
    """User game progress and statistics."""
    
    __tablename__ = 'user_progress'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # XP and Level
    total_xp = db.Column(db.Integer, default=0)
    current_level = db.Column(db.Integer, default=1)
    current_rank = db.Column(db.String(50), default='Tourist')
    
    # Statistics
    locations_visited = db.Column(db.Integer, default=0)
    photos_taken = db.Column(db.Integer, default=0)
    quests_completed = db.Column(db.Integer, default=0)
    achievements_earned = db.Column(db.Integer, default=0)
    
    # Georgian phrases learned (stored as JSON array)
    phrases_learned = db.Column(db.JSON, default=list)
    
    # Timestamps
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def add_xp(self, amount: int) -> dict:
        """Add XP and handle level up."""
        old_level = self.current_level
        self.total_xp += amount
        
        # Calculate new level
        new_level = 1
        for level, threshold in enumerate(LEVEL_THRESHOLDS, start=1):
            if self.total_xp >= threshold:
                new_level = level
        
        self.current_level = min(new_level, 10)
        self.current_rank = RANKS.get(self.current_level, 'Tourist')
        
        leveled_up = self.current_level > old_level
        
        return {
            'xp_gained': amount,
            'total_xp': self.total_xp,
            'new_level': self.current_level,
            'new_rank': self.current_rank,
            'leveled_up': leveled_up,
            'xp_to_next_level': self.xp_to_next_level(),
        }
    
    def xp_to_next_level(self) -> int:
        """Calculate XP needed for next level."""
        if self.current_level >= 10:
            return 0
        next_threshold = LEVEL_THRESHOLDS[self.current_level]
        return max(0, next_threshold - self.total_xp)
    
    def xp_progress_percent(self) -> float:
        """Calculate progress percentage to next level."""
        if self.current_level >= 10:
            return 100.0
        
        current_threshold = LEVEL_THRESHOLDS[self.current_level - 1]
        next_threshold = LEVEL_THRESHOLDS[self.current_level]
        level_xp = self.total_xp - current_threshold
        level_range = next_threshold - current_threshold
        
        return min(100.0, (level_xp / level_range) * 100)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_xp': self.total_xp,
            'current_level': self.current_level,
            'current_rank': self.current_rank,
            'locations_visited': self.locations_visited,
            'photos_taken': self.photos_taken,
            'quests_completed': self.quests_completed,
            'achievements_earned': self.achievements_earned,
            'phrases_learned': self.phrases_learned or [],
            'xp_to_next_level': self.xp_to_next_level(),
            'xp_progress_percent': self.xp_progress_percent(),
        }
    
    def __repr__(self):
        return f'<UserProgress {self.user_id} Level {self.current_level}>'





