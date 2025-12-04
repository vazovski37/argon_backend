"""
Game Service - Business Logic for Game Mechanics
"""
from app.models.user import User
from app.models.progress import UserProgress
from app.models.location import Location, UserLocationVisit
from app.models.achievement import Achievement, UserAchievement
from app.extensions import db


class GameService:
    """Handle all game-related business logic."""
    
    # XP rewards
    XP_VISIT_LOCATION = 50
    XP_LEARN_PHRASE = 15
    XP_COMPLETE_QUEST = 200
    XP_TAKE_PHOTO = 10
    
    @staticmethod
    def visit_location(user_id: str, location_id: str) -> dict:
        """
        Record a location visit, award XP, and check achievements.
        
        Returns:
            dict with success status, XP earned, and any new achievements
        """
        user = User.query.get(user_id)
        location = Location.query.get(location_id)
        
        if not user or not location:
            return {
                'success': False,
                'message': 'User or location not found',
                'xp_earned': 0
            }
        
        # Check if already visited
        existing = UserLocationVisit.query.filter_by(
            user_id=user_id,
            location_id=location_id
        ).first()
        
        if existing:
            return {
                'success': True,
                'message': f'Already visited {location.name}',
                'xp_earned': 0,
                'location': location.to_dict()
            }
        
        # Record the visit
        visit = UserLocationVisit(user_id=user_id, location_id=location_id)
        db.session.add(visit)
        
        # Award XP
        progress = user.progress
        xp_to_award = location.xp_reward or GameService.XP_VISIT_LOCATION
        xp_result = progress.add_xp(xp_to_award)
        
        # Update stats
        progress.locations_visited += 1
        
        # Check for achievements
        new_achievements = GameService._check_visit_achievements(user_id, progress)
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Visited {location.name}!',
            'xp_earned': xp_to_award,
            'location': location.to_dict(),
            'new_achievements': [a.name for a in new_achievements],
            'level_up': xp_result.get('leveled_up', False),
            'new_level': xp_result.get('new_level'),
            'new_rank': xp_result.get('new_rank'),
        }
    
    @staticmethod
    def learn_phrase(user_id: str, phrase: str, meaning: str = '') -> dict:
        """
        Record a learned phrase and award XP.
        
        Returns:
            dict with success status and XP earned
        """
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'User not found', 'xp_earned': 0}
        
        progress = user.progress
        
        # Check if already learned
        if progress.phrases_learned and phrase in progress.phrases_learned:
            return {
                'success': True,
                'message': f'You already learned "{phrase}"',
                'xp_earned': 0
            }
        
        # Add phrase
        if not progress.phrases_learned:
            progress.phrases_learned = []
        progress.phrases_learned = progress.phrases_learned + [phrase]
        
        # Award XP
        xp_result = progress.add_xp(GameService.XP_LEARN_PHRASE)
        
        # Check for achievements
        new_achievements = GameService._check_phrase_achievements(user_id, progress)
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Learned "{phrase}" ({meaning})',
            'phrase': phrase,
            'meaning': meaning,
            'xp_earned': GameService.XP_LEARN_PHRASE,
            'new_achievements': [a.name for a in new_achievements],
            'total_phrases': len(progress.phrases_learned),
        }
    
    @staticmethod
    def take_photo(user_id: str) -> dict:
        """Award XP for taking a photo."""
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'User not found', 'xp_earned': 0}
        
        progress = user.progress
        progress.photos_taken += 1
        xp_result = progress.add_xp(GameService.XP_TAKE_PHOTO)
        
        # Check achievements
        new_achievements = GameService._check_photo_achievements(user_id, progress)
        
        db.session.commit()
        
        return {
            'success': True,
            'xp_earned': GameService.XP_TAKE_PHOTO,
            'new_achievements': [a.name for a in new_achievements],
            'total_photos': progress.photos_taken,
        }
    
    @staticmethod
    def _check_visit_achievements(user_id: str, progress: UserProgress) -> list:
        """Check and award visit-based achievements."""
        new_achievements = []
        count = progress.locations_visited
        
        # Achievement definitions
        visit_achievements = [
            ('First Steps', 1, 'Visited your first location'),
            ('Explorer', 5, 'Visited 5 locations'),
            ('Adventurer', 10, 'Visited 10 locations'),
            ('Pathfinder', 25, 'Visited 25 locations'),
            ('Cartographer', 50, 'Visited 50 locations'),
        ]
        
        for name, required, desc in visit_achievements:
            if count >= required:
                achievement = GameService._award_achievement(user_id, name, desc, 'visits', required)
                if achievement:
                    new_achievements.append(achievement)
        
        return new_achievements
    
    @staticmethod
    def _check_phrase_achievements(user_id: str, progress: UserProgress) -> list:
        """Check and award phrase-based achievements."""
        new_achievements = []
        count = len(progress.phrases_learned or [])
        
        phrase_achievements = [
            ('First Words', 1, 'Learned your first Georgian phrase'),
            ('Linguist', 5, 'Learned 5 Georgian phrases'),
            ('Polyglot', 15, 'Learned 15 Georgian phrases'),
        ]
        
        for name, required, desc in phrase_achievements:
            if count >= required:
                achievement = GameService._award_achievement(user_id, name, desc, 'phrases', required)
                if achievement:
                    new_achievements.append(achievement)
        
        return new_achievements
    
    @staticmethod
    def _check_photo_achievements(user_id: str, progress: UserProgress) -> list:
        """Check and award photo-based achievements."""
        new_achievements = []
        count = progress.photos_taken
        
        photo_achievements = [
            ('Shutterbug', 1, 'Took your first photo'),
            ('Photographer', 10, 'Took 10 photos'),
            ('Visual Storyteller', 50, 'Took 50 photos'),
        ]
        
        for name, required, desc in photo_achievements:
            if count >= required:
                achievement = GameService._award_achievement(user_id, name, desc, 'photos', required)
                if achievement:
                    new_achievements.append(achievement)
        
        return new_achievements
    
    @staticmethod
    def _award_achievement(user_id: str, name: str, description: str, 
                          requirement_type: str, requirement_value: int) -> Achievement:
        """
        Award an achievement if not already earned.
        Creates the achievement if it doesn't exist.
        
        Returns:
            Achievement if newly awarded, None if already had it
        """
        # Find or create achievement
        achievement = Achievement.query.filter_by(name=name).first()
        if not achievement:
            achievement = Achievement(
                name=name,
                description=description,
                requirement_type=requirement_type,
                requirement_value=requirement_value,
                xp_reward=50 + (requirement_value * 10)  # Scale XP with difficulty
            )
            db.session.add(achievement)
            db.session.flush()
        
        # Check if user already has it
        existing = UserAchievement.query.filter_by(
            user_id=user_id,
            achievement_id=achievement.id
        ).first()
        
        if existing:
            return None
        
        # Award the achievement
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id
        )
        db.session.add(user_achievement)
        
        # Update user's achievement count
        user = User.query.get(user_id)
        if user and user.progress:
            user.progress.achievements_earned += 1
            # Award bonus XP for achievement
            user.progress.add_xp(achievement.xp_reward)
        
        return achievement




