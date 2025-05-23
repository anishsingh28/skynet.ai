import requests
import json
from fastapi import HTTPException, status
from config.settings import get_settings
import logging

# Get application settings
settings = get_settings()

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("firebase_auth")

class FirebaseAuthService:
    def __init__(self):
        self.api_key = settings.firebase.api_key
        print(self.api_key, "API KEY")
        self.base_url = "https://identitytoolkit.googleapis.com/v1/accounts"
        self.auth_domain = settings.firebase.auth_domain
        logger.info("Firebase Auth Service initialized")
    
    def sign_in_with_email_password(self, email: str, password: str):
        """
        Sign in a user with email and password using Firebase Auth REST API
        """
        logger.debug(f"Attempting to sign in user with email: {email}")
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        url = f"{self.base_url}:signInWithPassword?key={self.api_key}"
        
        try:
            logger.debug(f"Sending request to Firebase Auth API: {url}")
            # Add Content-Type header to ensure proper JSON parsing
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            response_data = response.json()
            
            if response.status_code != 200:
                error_message = response_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Login failed for email {email}: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Login failed: {error_message}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            logger.info(f"User signed in successfully: {response_data.get('localId')}")
            return response_data
        except requests.RequestException as e:
            logger.error(f"Request to Firebase Auth API failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication service unavailable: {str(e)}",
            )
    
    def sign_up_with_email_password(self, email: str, password: str):
        """
        Sign up a new user with email and password using Firebase Auth REST API
        """
        logger.debug(f"Attempting to sign up user with email: {email}")
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        url = f"{self.base_url}:signUp?key={self.api_key}"
        
        try:
            logger.debug(f"Sending request to Firebase Auth API: {url}")
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            response_data = response.json()
            
            if response.status_code != 200:
                error_message = response_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Signup failed for email {email}: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Signup failed: {error_message}",
                )
            
            logger.info(f"User signed up successfully: {response_data.get('localId')}")
            return response_data
        except requests.RequestException as e:
            logger.error(f"Request to Firebase Auth API failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication service unavailable: {str(e)}",
            )
    
    def update_profile(self, id_token: str, display_name: str = None, photo_url: str = None):
        """
        Update user profile using Firebase Auth REST API
        """
        logger.debug("Attempting to update user profile")
        payload = {
            "idToken": id_token,
        }
        
        if display_name:
            payload["displayName"] = display_name
        
        if photo_url:
            payload["photoUrl"] = photo_url
        
        url = f"{self.base_url}:update?key={self.api_key}"
        
        try:
            logger.debug(f"Sending request to Firebase Auth API: {url}")
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            response_data = response.json()
            
            if response.status_code != 200:
                error_message = response_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Profile update failed: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Profile update failed: {error_message}",
                )
            
            logger.info(f"User profile updated successfully: {response_data.get('localId')}")
            return response_data
        except requests.RequestException as e:
            logger.error(f"Request to Firebase Auth API failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication service unavailable: {str(e)}",
            )
    
    def sign_in_with_google(self, id_token: str):
        """
        Sign in or sign up a user with a Google ID token
        """
        logger.debug("Attempting to sign in with Google")
        payload = {
            "postBody": f"id_token={id_token}&providerId=google.com",
            "requestUri": f"{self.auth_domain}",
            "returnIdpCredential": True,
            "returnSecureToken": True
        }
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={self.api_key}"
        
        try:
            logger.debug(f"Sending request to Firebase Auth API: {url}")
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            response_data = response.json()
            
            if response.status_code != 200:
                error_message = response_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Google sign-in failed: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Google sign-in failed: {error_message}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            logger.info(f"User signed in with Google successfully: {response_data.get('localId')}")
            return response_data
        except requests.RequestException as e:
            logger.error(f"Request to Firebase Auth API failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication service unavailable: {str(e)}",
            )