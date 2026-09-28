from typing import Dict, Any, Optional
from backend.database import db

def assess_claim_verification(claim_answers: Dict[str, Any], found_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assists admins by comparing claimant's private verification answers against found item's true attributes.
    Does NOT auto-verify; returns an objective verification alignment score.
    """
    answers = claim_answers or {}
    points = 0
    total_checks = 4

    # 1. Brand match
    claim_brand = (answers.get("brand") or "").strip().lower()
    true_brand = (found_item.get("brand") or "").strip().lower()
    brand_match = False
    if true_brand and claim_brand:
        brand_match = (claim_brand == true_brand or claim_brand in true_brand or true_brand in claim_brand)
        if brand_match:
            points += 1

    # 2. Color match
    claim_color = (answers.get("color") or "").strip().lower()
    true_color = (found_item.get("color") or "").strip().lower()
    color_match = False
    if true_color and claim_color:
        color_match = (claim_color == true_color or claim_color in true_color or true_color in claim_color)
        if color_match:
            points += 1

    # 3. Location match
    claim_loc = (answers.get("lost_location") or "").strip().lower()
    true_loc = (found_item.get("location") or "").strip().lower()
    loc_match = False
    if true_loc and claim_loc:
        loc_match = (claim_loc == true_loc or claim_loc in true_loc or true_loc in claim_loc)
        if loc_match:
            points += 1

    # 4. Distinguishing features
    claim_feat = (answers.get("distinguishing_feature") or "").strip()
    feat_provided = len(claim_feat) >= 5
    if feat_provided:
        points += 1

    alignment_score = round(points / float(total_checks), 2)

    return {
        "alignment_score": alignment_score,
        "brand_match": brand_match,
        "color_match": color_match,
        "location_match": loc_match,
        "distinguishing_feature_provided": feat_provided
    }

def process_item_return(claim_id: str, admin_user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes the successful recovery flow:
    1. Mark claim as RETURNED
    2. Mark item as RETURNED
    3. Reward the finder with +50 Community Helper points and streak advancement
    4. Notify both owner and finder
    """
    claim = db.get_claim_by_id(claim_id)
    if not claim:
        raise ValueError(f"Claim with id {claim_id} not found.")

    item = db.get_item_by_id(claim["item_id"])
    if not item:
        raise ValueError("Associated item not found.")

    # Update claim status
    updated_claim = db.update_claim_status(
        claim_id=claim_id,
        new_status="RETURNED",
        reviewer_id=admin_user_id,
        notes="Item successfully verified and handed over to verified owner."
    )

    # Reward the finder
    finder_id = item["user_id"]
    gamification_res = db.record_activity_and_reward(finder_id, action="successful_return")

    # Send Notification to Finder
    db.create_notification(
        user_id=finder_id,
        title="Recovery Complete — Community Helper Reward!",
        message=f"The item '{item['title']}' you reported has been successfully returned to its owner! You earned +50 points and continued your streak.",
        notif_type="reward"
    )

    # Send Notification to Claimant
    db.create_notification(
        user_id=claim["claimant_id"],
        title="Belonging Recovered Successfully",
        message=f"Your claim for '{item['title']}' was verified and marked as returned. Thank you for using Back2You!",
        notif_type="claim"
    )

    return {
        "claim": updated_claim,
        "finder_rewards": gamification_res
    }
