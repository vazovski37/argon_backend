"""
Photos API
"""
from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import jwt_required, get_current_user
from werkzeug.utils import secure_filename
from app.models.photo import Photo, PhotoVisibility
from app.models.location import Location
from app.models.group import Group, GroupMember
from app.services.game_service import GameService
from app.services.storage_service import StorageService
from app.utils.geo import calculate_distance
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
    """Upload a new photo to Google Cloud Storage with auto-tagging."""
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
    
    # Get required GPS coordinates
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    
    if latitude is None or longitude is None:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    # Get optional data
    visibility = request.form.get('visibility', 'private').lower()
    group_id = request.form.get('group_id')
    caption = request.form.get('caption', '')
    is_selfie = request.form.get('is_selfie', 'false').lower() == 'true'
    
    # Validate visibility
    if visibility not in ['private', 'group', 'public']:
        return jsonify({'error': 'Invalid visibility. Must be: private, group, or public'}), 400
    
    # Validate group_id if visibility is 'group'
    if visibility == 'group':
        if not group_id:
            return jsonify({'error': 'group_id is required when visibility is "group"'}), 400
        
        # Check if group exists and user is a member
        group = Group.query.get(group_id)
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        
        is_member = GroupMember.query.filter_by(
            user_id=user.id,
            group_id=group_id
        ).first() is not None
        
        if not is_member:
            return jsonify({'error': 'You must be a member of the group to share photos'}), 403
    else:
        # Clear group_id if visibility is not 'group'
        group_id = None
    
    try:
        # Auto-tagging: Find nearest location within 50 meters
        location_id = None
        locations = Location.query.filter(
            Location.latitude.isnot(None),
            Location.longitude.isnot(None)
        ).all()
        
        min_distance = 50.0  # 50 meters threshold
        nearest_location = None
        
        for loc in locations:
            distance = calculate_distance(
                float(latitude),
                float(longitude),
                float(loc.latitude),
                float(loc.longitude)
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_location = loc
        
        if nearest_location:
            location_id = nearest_location.id
        
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
            group_id=group_id,
            file_path=upload_result['blob_path'],
            gcs_path=upload_result['blob_path'],
            file_name=secure_filename(file.filename),
            file_size=upload_result['file_size'],
            mime_type=upload_result['content_type'],
            caption=caption,
            is_selfie=is_selfie,
            visibility=visibility,
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
            'new_achievements': game_result.get('new_achievements', []),
            'auto_tagged_location': nearest_location.to_dict() if nearest_location else None
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


@photos_bp.route('/feed', methods=['GET'])
@jwt_required()
def get_photo_feed():
    """Get photo feed with filtering options."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    filter_type = request.args.get('filter', 'all').lower()
    group_id = request.args.get('group_id', type=str)
    
    try:
        query = Photo.query
        
        if filter_type == 'public':
            # Return all public photos
            query = query.filter_by(visibility='public')
        
        elif filter_type == 'group':
            # Return photos from groups the user is a member of
            if group_id:
                # Specific group
                is_member = GroupMember.query.filter_by(
                    user_id=user.id,
                    group_id=group_id
                ).first() is not None
                
                if not is_member:
                    return jsonify({'error': 'You are not a member of this group'}), 403
                
                query = query.filter(
                    Photo.visibility == 'group',
                    Photo.group_id == group_id
                )
            else:
                # All groups user is member of
                user_groups = GroupMember.query.filter_by(user_id=user.id).all()
                group_ids = [gm.group_id for gm in user_groups]
                
                if not group_ids:
                    return jsonify({
                        'photos': [],
                        'total': 0,
                        'message': 'You are not a member of any groups'
                    }), 200
                
                query = query.filter(
                    Photo.visibility == 'group',
                    Photo.group_id.in_(group_ids)
                )
        
        elif filter_type == 'private':
            # Return only current user's photos
            query = query.filter_by(user_id=user.id)
        
        else:  # 'all' - return all photos user can see
            # Public photos + user's own photos + group photos from groups user is in
            user_groups = GroupMember.query.filter_by(user_id=user.id).all()
            group_ids = [gm.group_id for gm in user_groups]
            
            # Build OR conditions
            conditions = [
                Photo.visibility == 'public',
                Photo.user_id == user.id
            ]
            
            # Add group photos condition only if user is in groups
            if group_ids:
                conditions.append(
                    db.and_(
                        Photo.visibility == 'group',
                        Photo.group_id.in_(group_ids)
                    )
                )
            
            query = query.filter(db.or_(*conditions))
        
        # Order by upload date (newest first)
        photos = query.order_by(Photo.uploaded_at.desc()).all()
        
        return jsonify({
            'photos': [p.to_dict() for p in photos],
            'total': len(photos),
            'filter': filter_type
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch feed: {str(e)}'}), 500


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



