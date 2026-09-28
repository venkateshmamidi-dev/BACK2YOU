from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from backend.database import db
from backend.models.schemas import ClaimCreate, ClaimUpdate, ClaimResponse
from backend.api.auth import get_current_user, get_admin_user
from backend.services.verification import assess_claim_verification, process_item_return

router = APIRouter(prefix="/claims", tags=["Claims & Verification"])

@router.post("", response_model=ClaimResponse)
def submit_claim(
    claim_in: ClaimCreate,
    current_user: dict = Depends(get_current_user)
):
    item = db.get_item_by_id(claim_in.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")

    if item["user_id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot submit a claim for an item you reported.")

    # Check for duplicate claim by same user
    existing_claims = db.list_claims(claimant_id=current_user["id"])
    for c in existing_claims:
        if c["item_id"] == claim_in.item_id and c["status"] in ["PENDING", "UNDER_REVIEW", "VERIFIED"]:
            raise HTTPException(
                status_code=400,
                detail="You have already submitted an active claim for this item."
            )

    claim_dict = {
        "match_id": claim_in.match_id,
        "item_id": claim_in.item_id,
        "claimant_id": current_user["id"],
        "verification_answers": claim_in.verification_answers.model_dump()
    }

    created = db.create_claim(claim_dict)

    # In-app notification to the item reporter
    db.create_notification(
        user_id=item["user_id"],
        title="New Ownership Claim Received",
        message=f"A student submitted a verification claim for '{item['title']}'. An admin is reviewing it.",
        notif_type="claim"
    )

    return created

@router.get("", response_model=List[ClaimResponse])
def get_user_or_all_claims(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    # Admins see all claims, regular users see only their submitted claims
    if current_user.get("role") in ["ADMIN", "MODERATOR"]:
        return db.list_claims(status=status)
    else:
        return db.list_claims(status=status, claimant_id=current_user["id"])

@router.get("/{claim_id}")
def get_claim_details(
    claim_id: str,
    current_user: dict = Depends(get_current_user)
):
    claim = db.get_claim_by_id(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    # Ensure access rights
    if claim["claimant_id"] != current_user["id"] and current_user.get("role") not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to this claim.")

    item = db.get_item_by_id(claim["item_id"])

    # If admin, evaluate automatic verification alignment
    verification_assessment = None
    if current_user.get("role") in ["ADMIN", "MODERATOR"] and item:
        verification_assessment = assess_claim_verification(claim["verification_answers"], item)

    return {
        "claim": claim,
        "item": item,
        "verification_assessment": verification_assessment
    }

@router.patch("/{claim_id}", response_model=ClaimResponse)
def update_claim(
    claim_id: str,
    updates: ClaimUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    existing = db.get_claim_by_id(claim_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Claim not found.")

    if updates.status == "RETURNED":
        # Run the full recovery completion flow
        res = process_item_return(claim_id=claim_id, admin_user_id=admin_user["id"])
        return res["claim"]

    updated = db.update_claim_status(
        claim_id=claim_id,
        new_status=updates.status,
        reviewer_id=admin_user["id"],
        notes=updates.review_notes
    )

    # Send status change notification to claimant
    db.create_notification(
        user_id=existing["claimant_id"],
        title=f"Claim Status Update: {updates.status}",
        message=f"Your claim for '{existing['item_title']}' has been updated to: {updates.status}." + (f" Note: {updates.review_notes}" if updates.review_notes else ""),
        notif_type="claim"
    )

    return updated
