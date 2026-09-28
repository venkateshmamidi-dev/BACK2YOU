from typing import List
from fastapi import APIRouter, Depends, Query
from backend.models.schemas import GamificationProfile, LeaderboardEntry, BadgeResponse
from backend.services.gamification import get_user_gamification, get_campus_leaderboard
from backend.api.auth import get_current_user
from backend.database import db

router = APIRouter(prefix="/community", tags=["Community Helper"])

@router.get("/gamification", response_model=GamificationProfile)
def get_gamification(current_user: dict = Depends(get_current_user)):
    return get_user_gamification(current_user["id"])

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(limit: int = Query(15, ge=1, le=50)):
    return get_campus_leaderboard(limit=limit)

@router.get("/badges", response_model=List[BadgeResponse])
def get_all_badges(current_user: dict = Depends(get_current_user)):
    profile = get_user_gamification(current_user["id"])
    return profile["badges"]
