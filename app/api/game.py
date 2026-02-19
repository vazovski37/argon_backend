"""
Game Progress API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from app.models.progress import UserProgress
from app.models.location import Location, UserLocationVisit
from app.models.achievement import Achievement, UserAchievement
from app.services.game_service import GameService
from app.extensions import db

game_bp = Blueprint('game', __name__)


@game_bp.route('/progress', methods=['GET'])
@jwt_required()
def get_progress():
    """Get current user's game progress."""
    user = get_current_user()
    if not user or not user.progress:
        return jsonify({'error': 'Progress not found'}), 404
    
    return jsonify(user.progress.to_dict())


@game_bp.route('/visit-location', methods=['POST'])
@jwt_required()
def visit_location():
    """Record a location visit and award XP."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    location_id = data.get('location_id')
    location_name = data.get('location_name')
    
    # Find location by ID or name
    location = None
    if location_id:
        location = Location.query.get(location_id)
    elif location_name:
        # Fuzzy search by name
        location = Location.query.filter(
            Location.name.ilike(f'%{location_name}%')
        ).first()
    
    if not location:
        return jsonify({
            'success': False,
            'message': 'Location not found',
            'xp_earned': 0
        }), 404
    
    # Check if already visited
    existing_visit = UserLocationVisit.query.filter_by(
        user_id=user.id,
        location_id=location.id
    ).first()
    
    if existing_visit:
        return jsonify({
            'success': True,
            'message': f'You have already visited {location.name}',
            'xp_earned': 0,
            'location': location.to_dict()
        })
    
    # Record visit
    result = GameService.visit_location(user.id, location.id)
    
    return jsonify(result)


@game_bp.route('/learn-phrase', methods=['POST'])
@jwt_required()
def learn_phrase():
    """Record a learned Georgian phrase."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    phrase = data.get('phrase', '').strip()
    meaning = data.get('meaning', '').strip()
    
    if not phrase:
        return jsonify({'error': 'Phrase is required'}), 400
    
    result = GameService.learn_phrase(user.id, phrase, meaning)
    
    return jsonify(result)


@game_bp.route('/achievements', methods=['GET'])
@jwt_required()
def get_achievements():
    """Get all achievements and user's earned achievements."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get all achievements
    all_achievements = Achievement.query.all()
    
    # Get user's earned achievements
    user_achievements = UserAchievement.query.filter_by(user_id=user.id).all()
    earned_ids = {ua.achievement_id for ua in user_achievements}
    
    # Build response
    achievements = []
    for achievement in all_achievements:
        data = achievement.to_dict()
        data['earned'] = achievement.id in earned_ids
        if achievement.id in earned_ids:
            ua = next((ua for ua in user_achievements if ua.achievement_id == achievement.id), None)
            data['earned_at'] = ua.earned_at.isoformat() if ua else None
        achievements.append(data)
    
    return jsonify({
        'achievements': achievements,
        'total_earned': len(earned_ids),
        'total_available': len(all_achievements)
    })


@game_bp.route('/visited-locations', methods=['GET'])
@jwt_required()
def get_visited_locations():
    """Get all locations user has visited."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    visits = UserLocationVisit.query.filter_by(user_id=user.id).all()
    
    return jsonify({
        'visits': [v.to_dict() for v in visits],
        'total': len(visits)
    })


@game_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get detailed user statistics."""
    user = get_current_user()
    if not user or not user.progress:
        return jsonify({'error': 'User not found'}), 404
    
    progress = user.progress
    
    # Get counts
    visits_count = UserLocationVisit.query.filter_by(user_id=user.id).count()
    achievements_count = UserAchievement.query.filter_by(user_id=user.id).count()
    
    return jsonify({
        'level': progress.current_level,
        'rank': progress.current_rank,
        'total_xp': progress.total_xp,
        'xp_to_next_level': progress.xp_to_next_level(),
        'xp_progress_percent': progress.xp_progress_percent(),
        'locations_visited': visits_count,
        'achievements_earned': achievements_count,
        'quests_completed': progress.quests_completed,
        'photos_taken': progress.photos_taken,
        'phrases_learned': len(progress.phrases_learned or []),
    })


@game_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get the global leaderboard."""
    limit = request.args.get('limit', 10, type=int)
    
    # Get top users by XP
    top_users = UserProgress.query.order_by(
        UserProgress.total_xp.desc()
    ).limit(limit).all()
    
    leaderboard = []
    for i, progress in enumerate(top_users, 1):
        user = progress.user
        leaderboard.append({
            'rank': i,
            'user_id': user.id,
            'name': user.name or 'Anonymous',
            'avatar_url': user.avatar_url,
            'level': progress.current_level,
            'title': progress.current_rank,
            'total_xp': progress.total_xp,
            'locations_visited': progress.locations_visited,
        })
    
    return jsonify({'leaderboard': leaderboard})





