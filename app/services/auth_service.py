import firebase_admin
from firebase_admin import credentials, auth, firestore
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from typing import Dict, Optional
from config.settings import get_settings

# Get application settings
settings = get_settings()

# Initialize Firebase Admin
cred = credentials.Certificate(settings.firebase.credentials_path)
firebase_app = firebase_admin.initialize_app(cred) 
db = firestore.client()

security = HTTPBearer()

# 1. User Authentication Functions
async def register_user(email: str, password: str, display_name: str = None) -> Dict:
    """Register a new user with email and password"""
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=False
        )
        
        # Create user profile in Firestore
        user_ref = db.collection('users').document(user.uid)
        user_ref.set({
            'email': email,
            'displayName': display_name or '',
            'createdAt': firestore.SERVER_TIMESTAMP,
            'role': 'user'
        })
        
        return {
            "status": "success",
            "message": "User registered successfully",
            "user_id": user.uid
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify Firebase ID token"""
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email", ""),
            "role": decoded_token.get("role", "user")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def refresh_token(refresh_token: str) -> Dict:
    """Refresh Firebase ID token"""
    try:
        # Note: Firebase Admin SDK doesn't directly support refresh tokens
        # This would typically be handled on the client side with Firebase SDK
        # This function is a placeholder for custom token refresh logic
        return {
            "status": "error",
            "message": "Token refresh should be handled by the Firebase client SDK"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# 3. Profile Management
async def get_user_profile(user_id: str) -> Dict:
    """Get user profile from Firestore"""
    try:
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            return {
                "status": "success",
                "profile": user_doc.to_dict()
            }
        else:
            return {
                "status": "error",
                "message": "User profile not found"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

async def update_user_profile(user_id: str, profile_data: Dict) -> Dict:
    """Update user profile in Firestore"""
    try:
        # Remove sensitive fields that shouldn't be updated directly
        if 'role' in profile_data:
            del profile_data['role']
            
        user_ref = db.collection('users').document(user_id)
        user_ref.update(profile_data)
        
        return {
            "status": "success",
            "message": "Profile updated successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
