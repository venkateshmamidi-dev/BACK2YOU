from typing import Dict, Any, List
from backend.database import db

def get_user_gamification(user_id: str) -> Dict[str, Any]:
    return db.get_gamification_profile(user_id)

def get_campus_leaderboard(limit: int = 15) -> List[Dict[str, Any]]:
    return db.get_leaderboard(limit=limit)

def reward_user_activity(user_id: str, activity_type: str) -> Dict[str, Any]:
    return db.record_activity_and_reward(user_id, activity_type)
