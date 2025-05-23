from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict

# Import both authentication services
from services.auth_service import (
    verify_token, 
    get_user_profile,
    update_user_profile
)
from services.firebase_auth_service import FirebaseAuthService

router = APIRouter(prefix="/auth")
firebase_auth = FirebaseAuthService()
 
class UserRegistration(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class TokenRefresh(BaseModel):
    refresh_token: str

class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

@router.post("/register")
async def register(user_data: UserRegistration):
    """Register a new user with email and password"""
    try:
        # Use the REST API service for registration
        result = firebase_auth.sign_up_with_email_password(
            email=user_data.email,
            password=user_data.password
        )
        
        # Create user profile in Firestore (still using the Admin SDK)
        user_id = result.get("localId")
        if user_id and user_data.display_name:
            # Update profile with display name
            firebase_auth.update_profile(
                id_token=result.get("idToken"),
                display_name=user_data.display_name
            )
        
        return JSONResponse(content={
            "status": "success",
            "message": "User registered successfully",
            "user_id": user_id,
            "id_token": result.get("idToken"),
            "refresh_token": result.get("refreshToken")
        })
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"status": "error", "message": e.detail}
        )
 
@router.post("/login")
async def login(user_data: UserLogin):
    """Login with email and password"""
    try:
        result = firebase_auth.sign_in_with_email_password(
            email=user_data.email,
            password=user_data.password
        )
        
        return JSONResponse(content={
            "status": "success",
            "message": "Login successful",
            "user_id": result.get("localId"),
            "id_token": result.get("idToken"),
            "refresh_token": result.get("refreshToken")
        })
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"status": "error", "message": e.detail}
        )

@router.post("/google")
async def google_sign_in(id_token: str):
    """Sign in with Google"""
    try:
        result = firebase_auth.sign_in_with_google(id_token)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Google sign-in successful",
            "user_id": result.get("localId"),
            "id_token": result.get("idToken"),
            "refresh_token": result.get("refreshToken")
        })
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"status": "error", "message": e.detail}
        )

@router.get("/profile")
async def get_profile(user: Dict = Depends(verify_token)):
    """Get user profile"""
    result = await get_user_profile(user["uid"])
    
    if result["status"] == "error":
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=result
        )
    
    return JSONResponse(content=result)

@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    user: Dict = Depends(verify_token)
):
    """Update user profile"""
    result = await update_user_profile(
        user_id=user["uid"],
        profile_data=profile_data.dict(exclude_unset=True)
    )
    
    if result["status"] == "error":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=result
        )
    
    return JSONResponse(content=result)