"""
Quests API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from app.models.quest import Quest, UserQuest
from app.models.progress import UserProgress
from app.extensions import db

quests_bp = Blueprint('quests', __name__)


@quests_bp.route('/', methods=['GET'])
def get_all_quests():
    """Get all available quests."""
    include_daily = request.args.get('daily', 'true').lower() == 'true'
    
    query = Quest.query
    if not include_daily:
        query = query.filter_by(is_daily=False)
    
    quests = query.all()
    
    return jsonify({
        'quests': [q.to_dict() for q in quests],
        'total': len(quests)
    })


@quests_bp.route('/<quest_id>', methods=['GET'])
def get_quest(quest_id: str):
    """Get a single quest by ID."""
    quest = Quest.query.get_or_404(quest_id)
    return jsonify(quest.to_dict())


@quests_bp.route('/my-quests', methods=['GET'])
@jwt_required()
def get_user_quests():
    """Get current user's quests (active and completed)."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user_quests = UserQuest.query.filter_by(user_id=user.id).all()
    
    active = [uq.to_dict() for uq in user_quests if uq.status == 'active']
    completed = [uq.to_dict() for uq in user_quests if uq.status == 'completed']
    
    return jsonify({
        'active': active,
        'completed': completed,
        'total_active': len(active),
        'total_completed': len(completed)
    })


@quests_bp.route('/<quest_id>/start', methods=['POST'])
@jwt_required()
def start_quest(quest_id: str):
    """Start a quest for the current user."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    quest = Quest.query.get_or_404(quest_id)
    
    # Check if already started
    existing = UserQuest.query.filter_by(
        user_id=user.id,
        quest_id=quest_id
    ).first()
    
    if existing:
        if existing.status == 'completed':
            return jsonify({
                'success': False,
                'message': f'You have already completed "{quest.name}"'
            }), 400
        return jsonify({
            'success': True,
            'message': f'You have already started "{quest.name}"',
            'user_quest': existing.to_dict()
        })
    
    # Create user quest
    user_quest = UserQuest(
        user_id=user.id,
        quest_id=quest_id,
        status='active',
        current_step=0
    )
    db.session.add(user_quest)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Started quest: {quest.name}',
        'user_quest': user_quest.to_dict(),
        'story_intro': quest.story_intro
    })


@quests_bp.route('/<quest_id>/advance', methods=['POST'])
@jwt_required()
def advance_quest(quest_id: str):
    """Advance to the next step in a quest."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user_quest = UserQuest.query.filter_by(
        user_id=user.id,
        quest_id=quest_id,
        status='active'
    ).first()
    
    if not user_quest:
        return jsonify({
            'success': False,
            'message': 'Quest not found or not active'
        }), 404
    
    quest = user_quest.quest
    completed = user_quest.advance_step()
    
    result = {
        'success': True,
        'current_step': user_quest.current_step,
        'completed': completed,
        'user_quest': user_quest.to_dict()
    }
    
    if completed:
        # Award XP for completing quest
        progress = user.progress
        xp_result = progress.add_xp(quest.xp_reward)
        progress.quests_completed += 1
        
        result['xp_earned'] = quest.xp_reward
        result['level_up'] = xp_result.get('leveled_up', False)
        result['new_level'] = xp_result.get('new_level')
        result['new_rank'] = xp_result.get('new_rank')
        result['message'] = f'Completed quest: {quest.name}! Earned {quest.xp_reward} XP.'
    else:
        result['message'] = f'Advanced to step {user_quest.current_step + 1}'
        if quest.steps and user_quest.current_step < len(quest.steps):
            result['next_step'] = quest.steps[user_quest.current_step]
    
    db.session.commit()
    
    return jsonify(result)


@quests_bp.route('/<quest_id>/abandon', methods=['POST'])
@jwt_required()
def abandon_quest(quest_id: str):
    """Abandon an active quest."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user_quest = UserQuest.query.filter_by(
        user_id=user.id,
        quest_id=quest_id,
        status='active'
    ).first()
    
    if not user_quest:
        return jsonify({
            'success': False,
            'message': 'Quest not found or not active'
        }), 404
    
    user_quest.status = 'abandoned'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Quest abandoned'
    })


# Admin endpoints
@quests_bp.route('/', methods=['POST'])
@jwt_required()
def create_quest():
    """Create a new quest (admin only)."""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    
    quest = Quest(
        name=data.get('name'),
        description=data.get('description'),
        story_intro=data.get('story_intro'),
        xp_reward=data.get('xp_reward', 200),
        steps=data.get('steps', []),
        is_daily=data.get('is_daily', False),
        difficulty=data.get('difficulty', 'medium'),
        estimated_time=data.get('estimated_time')
    )
    
    db.session.add(quest)
    db.session.commit()
    
    return jsonify(quest.to_dict()), 201





