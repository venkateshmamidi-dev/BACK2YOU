from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.api.auth import get_current_user
from backend.database import db

router = APIRouter(prefix="/profile", tags=["User Profile"])

@router.get("")
def get_user_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    gamification = db.get_gamification_profile(user_id)
    items = db.list_items(user_id=user_id)

    lost_count = len([i for i in items if i["type"] == "lost"])
    found_count = len([i for i in items if i["type"] == "found"])
    returned_count = len([i for i in items if i["status"] == "RETURNED"])

    return {
        "user": {
            "id": current_user["id"],
            "name": current_user["name"],
            "email": current_user["email"],
            "role": current_user["role"],
            "created_at": current_user.get("created_at")
        },
        "stats": {
            "total_reports": len(items),
            "lost_reports": lost_count,
            "found_reports": found_count,
            "successful_recoveries": gamification.get("successful_returns", 0),
            "points": gamification.get("points", 0),
            "current_streak": gamification.get("current_streak", 0),
            "longest_streak": gamification.get("longest_streak", 0)
        },
        "badges": gamification.get("badges", []),
        "recent_reports": items[:5]
    }

@router.get("/stats")
def get_profile_stats(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    gamification = db.get_gamification_profile(user_id)
    items = db.list_items(user_id=user_id)

    return {
        "reports": len(items),
        "successful_recoveries": gamification.get("successful_returns", 0),
        "points": gamification.get("points", 0),
        "current_streak": gamification.get("current_streak", 0),
        "longest_streak": gamification.get("longest_streak", 0)
    }

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    student_id: Optional[str] = None
    department: Optional[str] = None
    year_of_study: Optional[str] = None

@router.patch("")
def update_profile(
    updates: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    update_data = {}
    if updates.full_name:
        update_data["name"] = updates.full_name
    if updates.avatar_url:
        update_data["avatar_url"] = updates.avatar_url
    
    updated = db.update_user_profile(current_user["id"], update_data)
    return {
        "status": "success",
        "message": "Profile updated successfully.",
        "user": updated,
        "full_name": updated["name"]
    }

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password")
def change_password(
    data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    if not db.verify_password(data.current_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
    
    new_hash = db.hash_password(data.new_password)
    db.update_user_password(current_user["id"], new_hash)
    return {"status": "success", "message": "Password updated successfully."}

