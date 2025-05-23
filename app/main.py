from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routes import summarizer, auth
from middleware.auth_middleware import firebase_auth_middleware
from config.settings import get_settings
settings = get_settings()
app = FastAPI(
    title=settings.app_name, 
    version=settings.app_version, 
    debug=settings.api.debug
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,  
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

# Add Firebase auth middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    return await firebase_auth_middleware(request, call_next) 
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Include routers
app.include_router(summarizer.router)
app.include_router(auth.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run( 
        "main:app", 
        host=settings.api.host, 
        port=settings.api.port, 
        reload=settings.api.reload
    )
    

    