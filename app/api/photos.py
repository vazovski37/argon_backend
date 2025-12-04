"""
Photos API
"""
from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import jwt_required, get_current_user
from werkzeug.utils import secure_filename
from app.models.photo import Photo
from app.models.location import Location
from app.services.game_service import GameService
from app.services.storage_service import StorageService
from app.extensions import db

photos_bp = Blueprint('photos', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@photos_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_photos():
    """Get current user's photos."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    photos = Photo.query.filter_by(user_id=user.id).order_by(Photo.uploaded_at.desc()).all()
    
    return jsonify({
        'photos': [p.to_dict() for p in photos],
        'total': len(photos)
    })


@photos_bp.route('/location/<location_id>', methods=['GET'])
def get_location_photos(location_id: str):
    """Get all photos for a location."""
    photos = Photo.query.filter_by(location_id=location_id).order_by(Photo.uploaded_at.desc()).all()
    
    return jsonify({
        'photos': [p.to_dict() for p in photos],
        'total': len(photos)
    })


@photos_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_photo():
    """Upload a new photo to Google Cloud Storage."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Get optional data
    location_id = request.form.get('location_id')
    caption = request.form.get('caption', '')
    is_selfie = request.form.get('is_selfie', 'false').lower() == 'true'
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    
    # Validate location if provided
    if location_id:
        location = Location.query.get(location_id)
        if not location:
            return jsonify({'error': 'Location not found'}), 404
    
    try:
        # Upload to Google Cloud Storage
        upload_result = StorageService.upload_file(
            file=file,
            filename=file.filename,
            folder=f"photos/{user.id}",
            content_type=file.content_type
        )
        
        # Create photo record
        photo = Photo(
            user_id=user.id,
            location_id=location_id,
            file_path=upload_result['blob_path'],
            file_name=secure_filename(file.filename),
            file_size=upload_result['file_size'],
            mime_type=upload_result['content_type'],
            caption=caption,
            is_selfie=is_selfie,
            latitude=latitude,
            longitude=longitude,
            gcs_url=upload_result['public_url']
        )
        
        db.session.add(photo)
        
        # Award XP for taking photo
        game_result = GameService.take_photo(user.id)
        
        db.session.commit()
        
        return jsonify({
            'photo': photo.to_dict(),
            'xp_earned': game_result.get('xp_earned', 0),
            'new_achievements': game_result.get('new_achievements', [])
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@photos_bp.route('/<photo_id>', methods=['DELETE'])
@jwt_required()
def delete_photo(photo_id: str):
    """Delete a photo from Google Cloud Storage."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    photo = Photo.query.get_or_404(photo_id)
    
    # Check ownership
    if photo.user_id != user.id and not user.is_admin:
        return jsonify({'error': 'Not authorized'}), 403
    
    try:
        # Delete from GCS
        StorageService.delete_file(photo.file_path)
        
        db.session.delete(photo)
        db.session.commit()
        
        return jsonify({'message': 'Photo deleted'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500


@photos_bp.route('/file/<path:filepath>')
def serve_photo(filepath: str):
    """Redirect to the GCS public URL for the photo."""
    photo = Photo.query.filter_by(file_path=filepath).first()
    
    if photo and photo.gcs_url:
        return redirect(photo.gcs_url)
    
    # Fallback: generate URL from filepath
    from flask import current_app
    bucket_name = current_app.config.get('GCS_BUCKET', 'argonauts-photos')
    return redirect(f"https://storage.googleapis.com/{bucket_name}/{filepath}")



