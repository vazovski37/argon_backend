"""
Location and Visit Models
"""
from datetime import datetime
from uuid import uuid4
from app.extensions import db


class Location(db.Model):
    """Points of interest in Poti."""
    
    __tablename__ = 'locations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(255), nullable=False)
    name_ka = db.Column(db.String(255), nullable=True)  # Georgian name
    description = db.Column(db.Text, nullable=True)
    
    # Category: attraction, restaurant, landmark, nature, historical
    category = db.Column(db.String(50), default='attraction')
    
    # Location coordinates
    latitude = db.Column(db.Numeric(10, 8), nullable=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=True)
    
    # Game mechanics
    xp_reward = db.Column(db.Integer, default=50)
    
    # Media
    image_url = db.Column(db.Text, nullable=True)
    
    # Additional data (opening hours, contact, etc.)
    extra_data = db.Column(db.JSON, default=dict)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    visits = db.relationship('UserLocationVisit', backref='location', cascade='all, delete-orphan')
    photos = db.relationship('Photo', backref='location')
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'name_ka': self.name_ka,
            'description': self.description,
            'category': self.category,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'xp_reward': self.xp_reward,
            'image_url': self.image_url,
            'metadata': self.extra_data or {},
        }
    
    def __repr__(self):
        return f'<Location {self.name}>'


class UserLocationVisit(db.Model):
    """Track user visits to locations."""
    
    __tablename__ = 'user_location_visits'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    location_id = db.Column(db.String(36), db.ForeignKey('locations.id', ondelete='CASCADE'), nullable=False)
    
    visited_at = db.Column(db.DateTime, default=datetime.utcnow)
    photo_url = db.Column(db.Text, nullable=True)
    
    # Unique constraint: user can only visit a location once
    __table_args__ = (
        db.UniqueConstraint('user_id', 'location_id', name='unique_user_location_visit'),
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'location_id': self.location_id,
            'visited_at': self.visited_at.isoformat() if self.visited_at else None,
            'photo_url': self.photo_url,
            'location': self.location.to_dict() if self.location else None,
        }
    
    def __repr__(self):
        return f'<UserLocationVisit {self.user_id} -> {self.location_id}>'




