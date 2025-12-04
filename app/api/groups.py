"""
Groups API for Argonaut Memories
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from app.models.group import Group, GroupMember
from app.extensions import db

groups_bp = Blueprint('groups', __name__)


@groups_bp.route('/create', methods=['POST'])
@jwt_required()
def create_group():
    """Create a new photo sharing group."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Group name is required'}), 400
    
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Group name cannot be empty'}), 400
    
    try:
        # Generate unique join code
        max_attempts = 10
        join_code = None
        for _ in range(max_attempts):
            code = Group.generate_join_code()
            if not Group.query.filter_by(join_code=code).first():
                join_code = code
                break
        
        if not join_code:
            return jsonify({'error': 'Failed to generate unique join code'}), 500
        
        # Create group
        group = Group(
            name=name,
            join_code=join_code,
            owner_id=user.id
        )
        db.session.add(group)
        db.session.flush()  # Get the group ID
        
        # Add creator as member
        member = GroupMember(
            user_id=user.id,
            group_id=group.id
        )
        db.session.add(member)
        
        db.session.commit()
        
        return jsonify({
            'group': group.to_dict(),
            'message': 'Group created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create group: {str(e)}'}), 500


@groups_bp.route('/join', methods=['POST'])
@jwt_required()
def join_group():
    """Join a group using a join code."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or 'join_code' not in data:
        return jsonify({'error': 'Join code is required'}), 400
    
    join_code = data.get('join_code', '').strip().upper()
    if len(join_code) != 6:
        return jsonify({'error': 'Invalid join code format'}), 400
    
    try:
        # Find group by join code
        group = Group.query.filter_by(join_code=join_code).first()
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        
        # Check if user is already a member
        existing_member = GroupMember.query.filter_by(
            user_id=user.id,
            group_id=group.id
        ).first()
        
        if existing_member:
            return jsonify({
                'group': group.to_dict(),
                'message': 'You are already a member of this group'
            }), 200
        
        # Add user as member
        member = GroupMember(
            user_id=user.id,
            group_id=group.id
        )
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'group': group.to_dict(),
            'message': 'Successfully joined group'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to join group: {str(e)}'}), 500


@groups_bp.route('/my-groups', methods=['GET'])
@jwt_required()
def get_my_groups():
    """Get all groups the current user is a member of."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        # Get all groups where user is a member
        memberships = GroupMember.query.filter_by(user_id=user.id).all()
        groups = [membership.group for membership in memberships]
        
        # Sort by created_at descending
        groups.sort(key=lambda g: g.created_at, reverse=True)
        
        return jsonify({
            'groups': [g.to_dict() for g in groups],
            'total': len(groups)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch groups: {str(e)}'}), 500


@groups_bp.route('/<group_id>', methods=['GET'])
@jwt_required()
def get_group(group_id: str):
    """Get details of a specific group."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        group = Group.query.get_or_404(group_id)
        
        # Check if user is a member
        is_member = GroupMember.query.filter_by(
            user_id=user.id,
            group_id=group.id
        ).first() is not None
        
        if not is_member and group.owner_id != user.id:
            return jsonify({'error': 'Not authorized to view this group'}), 403
        
        group_dict = group.to_dict()
        group_dict['is_member'] = is_member
        group_dict['is_owner'] = group.owner_id == user.id
        
        return jsonify({'group': group_dict}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch group: {str(e)}'}), 500


@groups_bp.route('/<group_id>/members', methods=['GET'])
@jwt_required()
def get_group_members(group_id: str):
    """Get all members of a group."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        group = Group.query.get_or_404(group_id)
        
        # Check if user is a member
        is_member = GroupMember.query.filter_by(
            user_id=user.id,
            group_id=group.id
        ).first() is not None
        
        if not is_member and group.owner_id != user.id:
            return jsonify({'error': 'Not authorized to view members'}), 403
        
        members = GroupMember.query.filter_by(group_id=group_id).all()
        
        return jsonify({
            'members': [m.to_dict() for m in members],
            'total': len(members)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch members: {str(e)}'}), 500

