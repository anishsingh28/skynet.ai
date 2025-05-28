from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv() 

class FirebaseSettings(BaseSettings):
    credentials_path: str = Field(default=os.getenv("FIREBASE_CREDENTIALS_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "serviceAccountKey.json")))
    storage_bucket: Optional[str] = Field(default=os.getenv("FIREBASE_STORAGE_BUCKET"))
    api_key: str = Field(default=os.getenv("FIREBASE_API_KEY", ""))
    auth_domain: str = Field(default=os.getenv("FIREBASE_AUTH_DOMAIN", ""))
    projectid: str = Field(default=os.getenv("FIREBASE_PROJECTID", ""))
    messagingsenderid: str = Field(default=os.getenv("FIREBASE_MESSAGINGSENDERID", ""))
    appid: str = Field(default=os.getenv("FIREBASE_APPID", ""))
    measurementid: str = Field(default=os.getenv("FIREBASE_MEASUREMENTID", ""))
      
    class Config:
        env_prefix = "FIREBASE_"

class LLMSettings(BaseSettings): 
    model: str = Field(default=os.getenv("LLM_MODEL"))
    endpoint: str = Field(default=os.getenv("LLM_ENDPOINT", "https://models.github.ai/inference"))
    token: str = Field(default=os.getenv("LLM_TOKEN"))
    temperature: float = Field(default=float(os.getenv("LLM_TEMPERATURE", "1.0")))
    
    class Config:
        env_prefix = "LLM_"

class APISettings(BaseSettings):
    host: str = Field(default=os.getenv("API_HOST", "0.0.0.0"))
    port: int = Field(default=int(os.getenv("API_PORT", "8000"))) 
    reload: bool = Field(default=os.getenv("API_RELOAD", "True").lower() == "true")
    debug: bool = Field(default=os.getenv("API_DEBUG", "False").lower() == "true")
    
    class Config:
        env_prefix = "API_"

class CORSSettings(BaseSettings):
    allow_origins: List[str] = Field(default=["*"])
    allow_credentials: bool = Field(default=True)
    allow_methods: List[str] = Field(default=["*"]) 
    allow_headers: List[str] = Field(default=["*"])
    
    class Config:
        env_prefix = "CORS_"

class Settings(BaseSettings):
    app_name: str = Field(default="skynet.ai")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    
    # Nested settings
    firebase: FirebaseSettings = FirebaseSettings()
    llm: LLMSettings = LLMSettings()
    api: APISettings = APISettings()
    cors: CORSSettings = CORSSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """
    Returns the application settings, using lru_cache to avoid 
    loading the settings multiple times.
    """
    return Settings()