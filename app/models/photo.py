"""
Photo Model
"""
from datetime import datetime
from uuid import uuid4
from app.extensions import db


class Photo(db.Model):
    """User uploaded photos."""
    
    __tablename__ = 'photos'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    location_id = db.Column(db.String(36), db.ForeignKey('locations.id', ondelete='SET NULL'), nullable=True)
    
    # File info
    file_path = db.Column(db.Text, nullable=False)  # GCS blob path
    file_name = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    mime_type = db.Column(db.String(50), nullable=True)
    gcs_url = db.Column(db.Text, nullable=True)  # Full GCS public URL
    
    # Photo metadata
    caption = db.Column(db.Text, nullable=True)
    is_selfie = db.Column(db.Boolean, default=False)
    
    # GPS coordinates when photo was taken
    latitude = db.Column(db.Numeric(10, 8), nullable=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=True)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_url(self) -> str:
        """Get the full URL for this photo."""
        if self.gcs_url:
            return self.gcs_url
        if self.file_path.startswith('http'):
            return self.file_path
        return f"https://storage.googleapis.com/{self.file_path}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'location_id': self.location_id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'url': self.get_url(),
            'caption': self.caption,
            'is_selfie': self.is_selfie,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'location': self.location.to_dict() if self.location else None,
        }
    
    def __repr__(self):
        return f'<Photo {self.id} by {self.user_id}>'




