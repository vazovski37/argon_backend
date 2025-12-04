"""
Locations API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user, jwt_required
from app.models.location import Location, UserLocationVisit
from app.extensions import db

locations_bp = Blueprint('locations', __name__)


@locations_bp.route('/', methods=['GET'])
def get_all_locations():
    """Get all locations."""
    category = request.args.get('category')
    
    query = Location.query
    if category:
        query = query.filter_by(category=category)
    
    locations = query.order_by(Location.name).all()
    
    return jsonify({
        'locations': [loc.to_dict() for loc in locations],
        'total': len(locations)
    })


@locations_bp.route('/<location_id>', methods=['GET'])
def get_location(location_id: str):
    """Get a single location by ID."""
    location = Location.query.get_or_404(location_id)
    return jsonify(location.to_dict())


@locations_bp.route('/search', methods=['GET'])
def search_locations():
    """Search locations by name."""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'locations': [], 'total': 0})
    
    locations = Location.query.filter(
        (Location.name.ilike(f'%{query}%')) |
        (Location.name_ka.ilike(f'%{query}%')) |
        (Location.description.ilike(f'%{query}%'))
    ).all()
    
    return jsonify({
        'locations': [loc.to_dict() for loc in locations],
        'total': len(locations)
    })


@locations_bp.route('/nearby', methods=['GET'])
def get_nearby_locations():
    """Get locations near a coordinate."""
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 5.0, type=float)  # km
    
    if lat is None or lng is None:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    # Simple distance calculation (not accurate for large distances)
    # For production, use PostGIS
    locations = Location.query.filter(
        Location.latitude.isnot(None),
        Location.longitude.isnot(None)
    ).all()
    
    nearby = []
    for loc in locations:
        # Approximate distance in km
        dist = ((float(loc.latitude) - lat) ** 2 + (float(loc.longitude) - lng) ** 2) ** 0.5 * 111
        if dist <= radius:
            data = loc.to_dict()
            data['distance_km'] = round(dist, 2)
            nearby.append(data)
    
    # Sort by distance
    nearby.sort(key=lambda x: x['distance_km'])
    
    return jsonify({
        'locations': nearby,
        'total': len(nearby)
    })


@locations_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all location categories with counts."""
    from sqlalchemy import func
    
    categories = db.session.query(
        Location.category,
        func.count(Location.id)
    ).group_by(Location.category).all()
    
    return jsonify({
        'categories': [
            {'name': cat, 'count': count}
            for cat, count in categories
        ]
    })


# Admin endpoints (require admin check in production)
@locations_bp.route('/', methods=['POST'])
@jwt_required()
def create_location():
    """Create a new location (admin only)."""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    
    location = Location(
        name=data.get('name'),
        name_ka=data.get('name_ka'),
        description=data.get('description'),
        category=data.get('category', 'attraction'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        xp_reward=data.get('xp_reward', 50),
        image_url=data.get('image_url'),
        metadata=data.get('metadata', {})
    )
    
    db.session.add(location)
    db.session.commit()
    
    return jsonify(location.to_dict()), 201


@locations_bp.route('/<location_id>', methods=['PUT'])
@jwt_required()
def update_location(location_id: str):
    """Update a location (admin only)."""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    location = Location.query.get_or_404(location_id)
    data = request.get_json()
    
    if 'name' in data:
        location.name = data['name']
    if 'name_ka' in data:
        location.name_ka = data['name_ka']
    if 'description' in data:
        location.description = data['description']
    if 'category' in data:
        location.category = data['category']
    if 'latitude' in data:
        location.latitude = data['latitude']
    if 'longitude' in data:
        location.longitude = data['longitude']
    if 'xp_reward' in data:
        location.xp_reward = data['xp_reward']
    if 'image_url' in data:
        location.image_url = data['image_url']
    if 'metadata' in data:
        location.metadata = data['metadata']
    
    db.session.commit()
    
    return jsonify(location.to_dict())


@locations_bp.route('/<location_id>', methods=['DELETE'])
@jwt_required()
def delete_location(location_id: str):
    """Delete a location (admin only)."""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    location = Location.query.get_or_404(location_id)
    db.session.delete(location)
    db.session.commit()
    
    return jsonify({'message': 'Location deleted'})




