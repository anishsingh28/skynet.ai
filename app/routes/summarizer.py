from fastapi import APIRouter, Request , File , UploadFile
from fastapi.responses import JSONResponse


from models.summarizer_model import Summarizermodel
from services import summarizer_service

router = APIRouter(prefix="/summarizer")

@router.get("/text")
async def summarize_text(user_input: Summarizermodel, request: Request):
    try:
        result = await summarizer_service.summarize_text(user_input=user_input, request=request) 
        return JSONResponse (content=result, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@router.post("/file")
async def summarize_file(request: Request, file: UploadFile = File(...)):
    try:
        result = await summarizer_service.summarize_file(file=file, request=request)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)