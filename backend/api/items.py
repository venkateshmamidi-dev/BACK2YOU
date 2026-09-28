import os
import uuid
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from backend.config import settings
from backend.database import db
from backend.models.schemas import ItemCreate, ItemUpdate, ItemResponse
from backend.api.auth import get_current_user
from backend.services.nlp import generate_text_embedding
from backend.services.vision import generate_image_embedding
from backend.services.matching import find_matches_for_item
from backend.services.gamification import reward_user_activity

router = APIRouter(prefix="/items", tags=["Items"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

from backend.database.supabase_client import get_supabase_client, is_supabase_configured

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Validates and stores uploaded item photos safely.
    Stores in Supabase Storage when configured, or local static storage fallback.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No image file provided.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Allowed formats: JPG, JPEG, PNG, WEBP, GIF."
        )

    # Validate file size
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB."
        )

    filename = f"{uuid.uuid4()}{ext}"

    # Supabase Storage if configured
    if is_supabase_configured():
        try:
            supabase = get_supabase_client()
            if supabase:
                bucket = settings.SUPABASE_STORAGE_BUCKET
                supabase.storage.from_(bucket).upload(filename, contents)
                public_url = supabase.storage.from_(bucket).get_public_url(filename)
                return {
                    "status": "success",
                    "image_url": public_url,
                    "filename": filename,
                    "storage": "supabase"
                }
        except Exception as e:
            print(f"[Storage] Supabase upload failed: {e}. Falling back to local disk storage.")

    # Local disk fallback
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unable to save image file locally.")

    relative_url = f"/uploads/{filename}"
    return {
        "status": "success",
        "image_url": relative_url,
        "filename": filename,
        "storage": "local"
    }

@router.get("/user/me", response_model=List[ItemResponse])
def get_current_user_items(
    item_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Returns all items reported by the currently authenticated user."""
    t = item_type.lower() if item_type else None
    return db.list_items(user_id=current_user["id"], item_type=t)

@router.post("/check-duplicate")
def check_duplicate_report(
    item_data: ItemCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Checks if the user has recently submitted an extremely similar report to avoid accidental duplicates.
    """
    user_items = db.list_items(user_id=current_user["id"], item_type=item_data.type)
    for existing in user_items:
        if (
            existing["category"].lower() == item_data.category.lower() and
            existing["location"].lower() == item_data.location.lower() and
            (
                existing["title"].lower() in item_data.title.lower() or
                item_data.title.lower() in existing["title"].lower()
            )
        ):
            return {
                "is_duplicate_suspected": True,
                "existing_item_id": existing["id"],
                "message": "Looks like you may already have a similar report on file."
            }
    return {"is_duplicate_suspected": False}

def process_item_ai_embeddings(item: dict):
    """Generates and persists Computer Vision and NLP embeddings for a newly created item."""
    text_content = f"{item['title']} {item['description']} {item.get('brand', '')} {item.get('color', '')} {item.get('distinguishing_features', '')}"
    txt_emb = generate_text_embedding(text_content)

    img_emb = None
    if item.get("image_url"):
        img_emb = generate_image_embedding(item["image_url"])

    db.save_item_embeddings(
        item_id=item["id"],
        image_embedding=img_emb,
        text_embedding=txt_emb,
        model_name="all-MiniLM-L6-v2 + MobileNetV3"
    )

@router.post("/lost", response_model=dict)
def report_lost_item(
    item_in: ItemCreate,
    current_user: dict = Depends(get_current_user)
):
    if item_in.type != "lost":
        raise HTTPException(status_code=400, detail="Endpoint expects item type 'lost'.")

    item_dict = item_in.model_dump()
    item_dict["user_id"] = current_user["id"]
    item = db.create_item(item_dict)

    # Process AI Embeddings asynchronously or synchronously
    try:
        process_item_ai_embeddings(item)
    except Exception as e:
        print(f"[Items] Error processing AI embeddings: {e}")

    # Immediately search for existing potential matches
    matches_result = {}
    try:
        matches_result = find_matches_for_item(item["id"], limit=5)
    except Exception as e:
        print(f"[Items] Matching search error: {e}")

    return {
        "status": "success",
        "message": "Lost item report registered successfully.",
        "item": item,
        "potential_matches": matches_result.get("matches", [])
    }

@router.post("/found", response_model=dict)
def report_found_item(
    item_in: ItemCreate,
    current_user: dict = Depends(get_current_user)
):
    if item_in.type != "found":
        raise HTTPException(status_code=400, detail="Endpoint expects item type 'found'.")

    item_dict = item_in.model_dump()
    item_dict["user_id"] = current_user["id"]
    item = db.create_item(item_dict)

    # Process AI Embeddings
    try:
        process_item_ai_embeddings(item)
    except Exception as e:
        print(f"[Items] Error processing AI embeddings: {e}")

    # Reward Finder with Community Helper points (+10 for reporting found item)
    rewards = reward_user_activity(current_user["id"], activity_type="found_report")

    # Search against existing active lost reports
    matches_result = {}
    try:
        matches_result = find_matches_for_item(item["id"], limit=5)
    except Exception as e:
        print(f"[Items] Matching search error: {e}")

    return {
        "status": "success",
        "message": "Found item report submitted. Thank you for helping the campus community!",
        "item": item,
        "potential_matches": matches_result.get("matches", []),
        "gamification": rewards
    }

@router.get("/lost", response_model=List[ItemResponse])
def get_lost_items(
    category: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(50, le=100)
):
    return db.list_items(
        item_type="lost",
        category=category,
        location=location,
        status=status,
        search_query=search,
        user_id=user_id,
        limit=limit
    )

@router.get("/found", response_model=List[ItemResponse])
def get_found_items(
    category: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(50, le=100)
):
    return db.list_items(
        item_type="found",
        category=category,
        location=location,
        status=status,
        search_query=search,
        user_id=user_id,
        limit=limit
    )

@router.get("/{item_id}", response_model=ItemResponse)
def get_item_by_id(item_id: str):
    item = db.get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return item

@router.patch("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: str,
    updates: ItemUpdate,
    current_user: dict = Depends(get_current_user)
):
    existing = db.get_item_by_id(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found.")

    if existing["user_id"] != current_user["id"] and current_user.get("role") not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(status_code=403, detail="You do not have permission to modify this report.")

    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    updated = db.update_item(item_id, update_dict)
    return updated

@router.delete("/{item_id}")
def delete_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    existing = db.get_item_by_id(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found.")

    if existing["user_id"] != current_user["id"] and current_user.get("role") not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(status_code=403, detail="Permission denied.")

    db.delete_item(item_id)
    return {"status": "success", "message": "Report deleted successfully."}
