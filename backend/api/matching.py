from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Depends
from backend.config import settings
from backend.models.schemas import MatchResponse, MatchWeightsConfig
from backend.services.matching import find_matches_for_item
from backend.api.auth import get_admin_user, get_current_user
from backend.database import db

router = APIRouter(prefix="/matching", tags=["Matching Engine"])

@router.get("", response_model=List[Dict[str, Any]])
def list_matches(
    limit: int = Query(20, ge=1, le=50),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0)
):
    """Returns top ranked potential matches in the campus system."""
    return db.list_all_matches(limit=limit, min_confidence=min_confidence)

@router.post("/find", response_model=MatchResponse)
def trigger_matching_engine(
    item_id: str = Query(..., description="ID of the lost or found item"),
    limit: int = Query(5, ge=1, le=10)
):
    try:
        results = find_matches_for_item(item_id=item_id, limit=limit)
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching calculation error: {str(e)}")

@router.get("/{item_id}", response_model=MatchResponse)
def get_item_matches(
    item_id: str,
    limit: int = Query(5, ge=1, le=10)
):
    try:
        results = find_matches_for_item(item_id=item_id, limit=limit)
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/weights/current", response_model=MatchWeightsConfig)
def get_current_weights():
    return {
        "weight_image": settings.WEIGHT_IMAGE,
        "weight_text": settings.WEIGHT_TEXT,
        "weight_location": settings.WEIGHT_LOCATION,
        "weight_time": settings.WEIGHT_TIME,
        "weight_attributes": settings.WEIGHT_ATTRIBUTES
    }

@router.post("/weights/update", response_model=MatchWeightsConfig)
def update_weights(
    weights: MatchWeightsConfig,
    admin_user: dict = Depends(get_admin_user)
):
    # Verify sum approximately 1.0
    total = sum([
        weights.weight_image,
        weights.weight_text,
        weights.weight_location,
        weights.weight_time,
        weights.weight_attributes
    ])
    if abs(total - 1.0) > 0.05:
        raise HTTPException(status_code=400, detail=f"Weights must sum to 1.0 (current sum: {round(total, 2)})")

    settings.WEIGHT_IMAGE = weights.weight_image
    settings.WEIGHT_TEXT = weights.weight_text
    settings.WEIGHT_LOCATION = weights.weight_location
    settings.WEIGHT_TIME = weights.weight_time
    settings.WEIGHT_ATTRIBUTES = weights.weight_attributes

    return weights
