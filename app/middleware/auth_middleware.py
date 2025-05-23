from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import firebase_admin
from firebase_admin import auth
from services.firebase_auth_service import FirebaseAuthService

# Initialize the Firebase Auth Service
firebase_auth = FirebaseAuthService()

async def firebase_auth_middleware(request: Request, call_next):
    """Middleware to verify Firebase ID tokens for protected routes"""
    
    # Skip authentication for non-protected routes
    if request.url.path in ["/", "/docs", "/openapi.json", "/auth/login", "/auth/register", "/auth/google"]:
        return await call_next(request)
    
    # Check for Authorization header
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing or invalid authentication token"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract and verify token
    token = authorization.replace("Bearer ", "")
    try:
        # Use Firebase Admin SDK for token verification
        decoded_token = auth.verify_id_token(token)
        # Add user info to request state
        request.state.user = {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email", ""),
            "role": decoded_token.get("role", "user")
        }
        return await call_next(request) 
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": f"Invalid authentication token: {str(e)}"},
            headers={"WWW-Authenticate": "Bearer"},
        )