from utils.llm import LLM
from models.summarizer_model import Summarizermodel
from fastapi import Request, File, UploadFile


from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

import tempfile
import os
import io
from PyPDF2 import PdfReader  



async def summarize_text(user_input: Summarizermodel, request: Request):
    try:
        # Generate cache key
        u_id = request.state.user["uid"]
        cache_key = f"summary:{u_id}:{hash(user_input.text)}"
        cached_summary = request.app.state.redis.get(cache_key)
        if not cached_summary:
            llm = LLM()
            model = llm.get_openai_model()
             # Create document from input text
            docs = [Document(page_content=user_input.text)]
            
            # Split text into manageable chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100
            )
            split_docs = text_splitter.split_documents(docs)
            
            # Use map_reduce for batch processing
            chain = load_summarize_chain(
                llm=model, 
                chain_type="map_reduce",  # Changed from "stuff" to "map_reduce"
                verbose=False
            )
            
            # Process in batches
            summary = await chain.arun(split_docs)
            
            # set value to redis
            request.app.state.redis.set(cache_key, summary, ex=3600)
        
       
        
           
            result = {
                "status": "success",
                "message": summary
                
            }
            return result
        if isinstance(cached_summary, bytes):
            cached_summary = cached_summary.decode('utf-8')
        
        result = {
            "status": "success",
            "message": summary,
            "message": cached_summary
           
        }
        
    except Exception as e:
        result = {
            "status": "error",
            "message": str(e)
        }
        return result
        
    
async def summarize_file(request: Request, file: UploadFile = File(...)):
    try:
        llm = LLM()
        model = llm.get_openai_model()
        
        content_type = file.content_type
        file_content = await file.read()
        cache_key = f"file_summary:{request.state.user['uid']}:{hash(file_content)}"
        cached_summary = request.app.state.redis.get(cache_key)
        
        if not cached_summary:

            if content_type == "application/pdf":
                pdf_reader = PdfReader(io.BytesIO(file_content))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                # Create document from extracted text
                docs = [Document(page_content=text)]
            elif content_type == "text/plain":
                text = file_content.decode("utf-8")
                docs = [Document(page_content=text)]
            else:
                result = {
                    "status": "error",
                    "message": "Unsupported file format. Please upload a PDF or TXT file."
                }
                return result
            
            # Split text into manageable chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100
            )
            split_docs = text_splitter.split_documents(docs)
            # Use map_reduce for batch processing
            chain = load_summarize_chain(
                llm=model,
                chain_type="map_reduce",  # Changed from "stuff" to "map_reduce"
                verbose=False
            )
            
            # Process in batches
            summary = await chain.arun(split_docs)
            
            # set value to redis
            request.app.state.redis.set(cache_key, summary, ex=3600)

        
            result = {
                "status": "success",
                "message": "summary"
            }
            return result
        if isinstance(cached_summary, bytes):
            cached_summary = cached_summary.decode('utf-8')
        
       
       
        return {
            "status": "success",
            "message": cached_summary
        }
        
       
        
    except Exception as e:
        result = {
            "status": "error",
            "message": str(e)
        }
        return result
        