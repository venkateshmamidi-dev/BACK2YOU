from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from jose import JWTError, jwt
from backend.config import settings
from backend.database import db
from backend.models.schemas import UserRegister, UserLogin, TokenResponse, UserProfile

router = APIRouter(prefix="/auth", tags=["Authentication"])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing or invalid format. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token subject.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid token.")

    user = db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User account not found.")
    return user

def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this operation."
        )
    return current_user

@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister):
    existing = db.get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this campus email already exists.")

    hashed_pw = db.hash_password(user_data.password)
    user = db.create_user(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_pw,
        role=user_data.role or "USER"
    )

    access_token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin):
    user = db.get_user_by_email(login_data.email)
    if not user or not db.verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    access_token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    profile = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "avatar_url": user.get("avatar_url"),
        "created_at": user.get("created_at")
    }
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": profile
    }

@router.get("/me", response_model=UserProfile)
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "avatar_url": current_user.get("avatar_url"),
        "created_at": current_user.get("created_at")
    }
