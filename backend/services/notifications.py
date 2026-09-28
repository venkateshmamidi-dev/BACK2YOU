from typing import List, Dict, Any
from backend.database import db

def notify_user(user_id: str, title: str, message: str, notif_type: str = "info") -> str:
    return db.create_notification(user_id, title, message, notif_type)

def list_notifications(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    return db.get_user_notifications(user_id, limit)

def mark_read(notif_id: str) -> bool:
    return db.mark_notification_read(notif_id)
