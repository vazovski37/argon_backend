"""
Group Models for Argonaut Memories
"""
from datetime import datetime
from uuid import uuid4
import string
import random
from app.extensions import db


class Group(db.Model):
    """Photo sharing groups."""
    
    __tablename__ = 'groups'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(255), nullable=False)
    join_code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = db.relationship('User', backref='owned_groups', foreign_keys=[owner_id])
    members = db.relationship('GroupMember', backref='group', cascade='all, delete-orphan')
    photos = db.relationship('Photo', backref='group')
    
    @staticmethod
    def generate_join_code() -> str:
        """Generate a random 6-character uppercase join code."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'join_code': self.join_code,
            'owner_id': self.owner_id,
            'owner': self.owner.to_dict() if self.owner else None,
            'member_count': len(self.members) if self.members else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<Group {self.name} ({self.join_code})>'


class GroupMember(db.Model):
    """Many-to-many relationship between users and groups."""
    
    __tablename__ = 'group_members'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    group_id = db.Column(db.String(36), db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: user cannot join the same group twice
    __table_args__ = (
        db.UniqueConstraint('user_id', 'group_id', name='unique_user_group'),
    )
    
    # Relationships
    user = db.relationship('User', backref='group_memberships')
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'group_id': self.group_id,
            'user': self.user.to_dict() if self.user else None,
            'group': self.group.to_dict() if self.group else None,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
        }
    
    def __repr__(self):
        return f'<GroupMember {self.user_id} -> {self.group_id}>'

