from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from pydantic import BaseModel, EmailStr, Field, field_validator

# User Schemas
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "USER"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

# Item Schemas
class ItemCreate(BaseModel):
    type: str = Field(...)
    title: str = Field(..., min_length=2, max_length=255)

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v):
        if isinstance(v, str):
            v_low = v.strip().lower()
            if v_low in ("lost", "found"):
                return v_low
        raise ValueError("Item type must be 'lost' or 'found'.")
    category: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=5)
    brand: Optional[str] = ""
    color: Optional[str] = ""
    distinguishing_features: Optional[str] = ""
    location: str = Field(..., min_length=2, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    event_date: str  # YYYY-MM-DD
    event_time: str  # HH:MM
    image_url: Optional[str] = None

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    distinguishing_features: Optional[str] = None

class ItemResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    type: str
    title: str
    category: str
    description: str
    brand: Optional[str] = ""
    color: Optional[str] = ""
    distinguishing_features: Optional[str] = ""
    image_url: Optional[str] = None
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    event_date: str
    event_time: str
    status: str
    created_at: str
    updated_at: Optional[str] = None

# Matching Schemas
class MatchBreakdown(BaseModel):
    image_similarity: float
    text_similarity: float
    category_similarity: float
    brand_similarity: float
    color_similarity: float
    location_similarity: float
    time_similarity: float
    final_confidence: float
    confidence_percentage: int
    confidence_level: str  # 'high', 'medium', 'low'
    explanation: List[str]

class MatchItem(BaseModel):
    match_id: Optional[str] = None
    item: ItemResponse
    breakdown: MatchBreakdown

class MatchResponse(BaseModel):
    query_item: ItemResponse
    matches: List[MatchItem]
    total_candidates_analyzed: int

class MatchWeightsConfig(BaseModel):
    weight_image: float = 0.40
    weight_text: float = 0.30
    weight_location: float = 0.15
    weight_time: float = 0.10
    weight_attributes: float = 0.05

# Claim Schemas
class VerificationAnswers(BaseModel):
    brand: Optional[str] = ""
    color: Optional[str] = ""
    lost_location: Optional[str] = ""
    approximate_time: Optional[str] = ""
    distinguishing_feature: Optional[str] = ""
    additional_proof: Optional[str] = ""

class ClaimCreate(BaseModel):
    match_id: Optional[str] = None
    item_id: str
    verification_answers: VerificationAnswers

class ClaimUpdate(BaseModel):
    status: str = Field(..., pattern="^(PENDING|UNDER_REVIEW|VERIFIED|REJECTED|RETURNED)$")
    review_notes: Optional[str] = None

class ClaimResponse(BaseModel):
    id: str
    match_id: Optional[str] = None
    item_id: str
    item_title: Optional[str] = None
    item_type: Optional[str] = None
    item_image: Optional[str] = None
    claimant_id: str
    claimant_name: Optional[str] = None
    claimant_email: Optional[str] = None
    verification_answers: Dict[str, Any]
    status: str
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

# Gamification Schemas
class BadgeResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    earned: bool = False
    earned_at: Optional[str] = None

class GamificationProfile(BaseModel):
    user_id: str
    current_streak: int
    longest_streak: int
    points: int
    verified_reports: int
    successful_returns: int
    last_activity: Optional[str] = None
    badges: List[BadgeResponse] = []

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    name: str
    points: int
    successful_returns: int
    verified_reports: int
    badges_count: int

# Notification Schemas
class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: str

# Admin Stats Schemas
class AdminStats(BaseModel):
    total_reports: int
    lost_items: int
    found_items: int
    potential_matches: int
    verified_claims: int
    returned_items: int
    active_users: int
    successful_recoveries: int
    successful_recovery_rate: float
    total_community_points: int
