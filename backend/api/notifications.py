from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.models.schemas import NotificationResponse
from backend.database import db
from backend.api.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_my_notifications(
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    notifs = db.get_user_notifications(user_id=current_user["id"], limit=limit)
    formatted = []
    for n in notifs:
        formatted.append({
            "id": n["id"],
            "user_id": n["user_id"],
            "title": n["title"],
            "message": n["message"],
            "type": n["type"],
            "is_read": bool(n["is_read"]),
            "created_at": n["created_at"]
        })
    return formatted

@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    success = db.mark_notification_read(notification_id)
    return {"status": "success", "is_read": True}

@router.post("/read-all")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    db.mark_all_notifications_read(current_user["id"])
    return {"status": "success", "message": "All notifications marked as read."}

