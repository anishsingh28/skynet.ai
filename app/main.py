from fastapi import FastAPI, Request
from routes import summarizer

app= FastAPI()

@app.get("/")
def hello():
    return {"Hello": "World"}

app.include_router(summarizer.router)
 

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app", port=8000, reload=True)
    
    