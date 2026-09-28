from typing import Dict, Any, List, Optional
from backend.config import settings
from backend.services.nlp import calculate_text_similarity, generate_text_embedding
from backend.services.vision import calculate_image_similarity, generate_image_embedding
from backend.services.location import calculate_location_similarity, calculate_time_similarity
from backend.database import db

def calculate_attribute_similarity(item1: Dict[str, Any], item2: Dict[str, Any]) -> Dict[str, float]:
    """
    Computes fine-grained attribute similarities: Category, Brand, Color.
    """
    # Category Match
    cat1 = (item1.get("category") or "").strip().lower()
    cat2 = (item2.get("category") or "").strip().lower()
    category_sim = 1.0 if cat1 == cat2 and cat1 != "" else (0.4 if cat1 in cat2 or cat2 in cat1 else 0.0)

    # Brand Match
    b1 = (item1.get("brand") or "").strip().lower()
    b2 = (item2.get("brand") or "").strip().lower()
    if b1 and b2:
        brand_sim = 1.0 if b1 == b2 else (0.8 if b1 in b2 or b2 in b1 else 0.0)
    else:
        brand_sim = 0.5  # Neutral if one is unspecified

    # Color Match
    c1 = (item1.get("color") or "").strip().lower()
    c2 = (item2.get("color") or "").strip().lower()
    if c1 and c2:
        words1 = set(c1.replace("/", " ").replace(",", " ").split())
        words2 = set(c2.replace("/", " ").replace(",", " ").split())
        overlap = words1.intersection(words2)
        color_sim = 1.0 if c1 == c2 else (0.85 if len(overlap) > 0 else 0.1)
    else:
        color_sim = 0.5

    return {
        "category_similarity": category_sim,
        "brand_similarity": brand_sim,
        "color_similarity": color_sim,
        "combined_attribute_similarity": (category_sim * 0.5 + brand_sim * 0.25 + color_sim * 0.25)
    }

def generate_match_explanation(
    lost_item: Dict[str, Any],
    found_item: Dict[str, Any],
    scores: Dict[str, float]
) -> List[str]:
    """
    Constructs explainable, human-readable reasons for why Back2You identified the match.
    """
    reasons = []

    # Category
    if scores.get("category_similarity", 0) >= 0.8:
        reasons.append(f"Identical category: {lost_item.get('category')}")
    
    # Brand
    b1 = lost_item.get("brand", "").strip()
    b2 = found_item.get("brand", "").strip()
    if b1 and b2 and scores.get("brand_similarity", 0) >= 0.8:
        reasons.append(f"Matching brand: {b1}")

    # Color
    c1 = lost_item.get("color", "").strip()
    c2 = found_item.get("color", "").strip()
    if c1 and c2 and scores.get("color_similarity", 0) >= 0.8:
        reasons.append(f"Matching color: {c1}")

    # Computer Vision
    img_sim = scores.get("image_similarity", 0)
    if img_sim >= 0.70:
        reasons.append(f"Strong visual resemblance detected by Computer Vision ({int(img_sim * 100)}%)")
    elif img_sim >= 0.50:
        reasons.append(f"Moderate visual similarity ({int(img_sim * 100)}%)")

    # NLP Semantic Description
    txt_sim = scores.get("text_similarity", 0)
    if txt_sim >= 0.65:
        reasons.append(f"High semantic overlap in item descriptions ({int(txt_sim * 100)}%)")

    # Location
    loc_sim = scores.get("location_similarity", 0)
    if loc_sim >= 0.95:
        reasons.append(f"Same reported campus location: {lost_item.get('location')}")
    elif loc_sim >= 0.70:
        reasons.append(f"Adjacent campus zones: {lost_item.get('location')} and {found_item.get('location')}")

    # Time
    time_sim = scores.get("time_similarity", 0)
    if time_sim >= 0.85:
        reasons.append("Close temporal correlation (reported within matching timeframe)")

    if not reasons:
        reasons.append("General category and campus proximity match")

    return reasons

def evaluate_match_pair(
    lost_item: Dict[str, Any],
    found_item: Dict[str, Any],
    lost_embeddings: Optional[Dict[str, Any]] = None,
    found_embeddings: Optional[Dict[str, Any]] = None,
    weights_override: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Computes all similarity dimensions and the weighted confidence score for a Lost-Found pair.
    """
    # 1. NLP Similarity
    text_sim = 0.0
    lost_txt_emb = lost_embeddings.get("text_embedding") if lost_embeddings else None
    found_txt_emb = found_embeddings.get("text_embedding") if found_embeddings else None

    if lost_txt_emb is None:
        lost_txt_emb = generate_text_embedding(f"{lost_item.get('title', '')} {lost_item.get('description', '')} {lost_item.get('brand', '')} {lost_item.get('color', '')}")
    if found_txt_emb is None:
        found_txt_emb = generate_text_embedding(f"{found_item.get('title', '')} {found_item.get('description', '')} {found_item.get('brand', '')} {found_item.get('color', '')}")

    text_sim = calculate_text_similarity(lost_txt_emb, found_txt_emb)

    # 2. Vision Similarity
    image_sim = 0.0
    has_image_pair = False
    lost_img_emb = lost_embeddings.get("image_embedding") if lost_embeddings else None
    found_img_emb = found_embeddings.get("image_embedding") if found_embeddings else None

    if lost_img_emb is not None and found_img_emb is not None:
        image_sim = calculate_image_similarity(lost_img_emb, found_img_emb)
        has_image_pair = True

    # 3. Attributes Similarity
    attr_scores = calculate_attribute_similarity(lost_item, found_item)
    category_sim = attr_scores["category_similarity"]
    brand_sim = attr_scores["brand_similarity"]
    color_sim = attr_scores["color_similarity"]
    attribute_sim = attr_scores["combined_attribute_similarity"]

    # 4. Location Similarity
    loc_sim = calculate_location_similarity(
        lost_item.get("location", ""),
        found_item.get("location", ""),
        lost_item.get("latitude"),
        lost_item.get("longitude"),
        found_item.get("latitude"),
        found_item.get("longitude")
    )

    # 5. Time Similarity
    time_sim = calculate_time_similarity(
        lost_item.get("event_date", ""),
        lost_item.get("event_time", ""),
        found_item.get("event_date", ""),
        found_item.get("event_time", "")
    )

    # Weights determination
    w_img = settings.WEIGHT_IMAGE
    w_txt = settings.WEIGHT_TEXT
    w_loc = settings.WEIGHT_LOCATION
    w_tim = settings.WEIGHT_TIME
    w_att = settings.WEIGHT_ATTRIBUTES

    if weights_override:
        w_img = weights_override.get("weight_image", w_img)
        w_txt = weights_override.get("weight_text", w_txt)
        w_loc = weights_override.get("weight_location", w_loc)
        w_tim = weights_override.get("weight_time", w_tim)
        w_att = weights_override.get("weight_attributes", w_att)

    # Dynamic reweighting if one or both items don't have images
    if not has_image_pair:
        total_remaining = w_txt + w_loc + w_tim + w_att
        w_txt_norm = w_txt / total_remaining
        w_loc_norm = w_loc / total_remaining
        w_tim_norm = w_tim / total_remaining
        w_att_norm = w_att / total_remaining
        final_score = (
            text_sim * w_txt_norm +
            loc_sim * w_loc_norm +
            time_sim * w_tim_norm +
            attribute_sim * w_att_norm
        )
    else:
        final_score = (
            image_sim * w_img +
            text_sim * w_txt +
            loc_sim * w_loc +
            time_sim * w_tim +
            attribute_sim * w_att
        )

    # Hard category mismatch penalty (e.g. laptop vs water bottle cannot be 85% match)
    if category_sim == 0.0:
        final_score = final_score * 0.35

    final_score = round(max(0.0, min(1.0, final_score)), 3)
    percentage = int(round(final_score * 100))

    if percentage >= 75:
        level = "high"
    elif percentage >= 50:
        level = "medium"
    else:
        level = "low"

    scores = {
        "image_similarity": round(image_sim, 3),
        "text_similarity": round(text_sim, 3),
        "category_similarity": round(category_sim, 3),
        "brand_similarity": round(brand_sim, 3),
        "color_similarity": round(color_sim, 3),
        "location_similarity": round(loc_sim, 3),
        "time_similarity": round(time_sim, 3),
        "final_confidence": final_score,
        "confidence_percentage": percentage,
        "confidence_level": level
    }

    scores["explanation"] = generate_match_explanation(lost_item, found_item, scores)
    return scores

def find_matches_for_item(
    item_id: str,
    limit: int = 5,
    min_confidence: float = 0.35,
    save_to_db: bool = True
) -> Dict[str, Any]:
    """
    Main matching engine entrypoint.
    Takes an item (either 'lost' or 'found') and searches all counter-items ('found' or 'lost').
    Ranks them from highest to lowest confidence score, returning top matches.
    """
    query_item = db.get_item_by_id(item_id)
    if not query_item:
        raise ValueError(f"Item with id {item_id} not found.")

    query_type = query_item["type"]
    target_type = "found" if query_type == "lost" else "lost"

    query_emb = db.get_item_embeddings(item_id)
    candidate_items = db.get_all_embeddings_by_type(target_type)

    results = []

    for candidate in candidate_items:
        # Avoid matching an item with itself or items owned by the same user if desired
        if candidate["id"] == query_item["id"]:
            continue

        cand_emb = {
            "image_embedding": candidate.get("image_embedding"),
            "text_embedding": candidate.get("text_embedding")
        }

        if query_type == "lost":
            breakdown = evaluate_match_pair(query_item, candidate, query_emb, cand_emb)
            lost_id, found_id = query_item["id"], candidate["id"]
        else:
            breakdown = evaluate_match_pair(candidate, query_item, cand_emb, query_emb)
            lost_id, found_id = candidate["id"], query_item["id"]

        if breakdown["final_confidence"] >= min_confidence:
            match_id = None
            if save_to_db:
                match_id = db.save_match({
                    "lost_item_id": lost_id,
                    "found_item_id": found_id,
                    "image_similarity": breakdown["image_similarity"],
                    "text_similarity": breakdown["text_similarity"],
                    "category_similarity": breakdown["category_similarity"],
                    "brand_similarity": breakdown["brand_similarity"],
                    "color_similarity": breakdown["color_similarity"],
                    "location_similarity": breakdown["location_similarity"],
                    "time_similarity": breakdown["time_similarity"],
                    "final_confidence": breakdown["final_confidence"],
                    "status": "POTENTIAL_MATCH"
                })

            results.append({
                "match_id": match_id,
                "item": candidate,
                "breakdown": breakdown
            })

    # Sort descending by final confidence
    results.sort(key=lambda x: x["breakdown"]["final_confidence"], reverse=True)
    top_matches = results[:limit]

    # If top match is found and confidence is high (>= 75%), notify the lost item owner!
    if top_matches and top_matches[0]["breakdown"]["final_confidence"] >= 0.70:
        top_m = top_matches[0]
        lost_user_id = query_item["user_id"] if query_type == "lost" else top_m["item"]["user_id"]
        pct = top_m["breakdown"]["confidence_percentage"]
        db.create_notification(
            user_id=lost_user_id,
            title="High-Confidence Match Identified",
            message=f"Back2You AI found a {pct}% confidence match for '{query_item['title']}'! Check your matches tab.",
            notif_type="match"
        )

    return {
        "query_item": query_item,
        "matches": top_matches,
        "total_candidates_analyzed": len(candidate_items)
    }
