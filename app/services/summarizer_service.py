from utils.llm import LLM
from  models.summarizer_model import Summarizermodel
from fastapi import Request

async def summarize_text(user_input: Summarizermodel, request: Request):
    try:
        llm = LLM()
        model = llm.get_openai_model()
        
        prompt = f"""
            summarize this text below.
            
            text:{user_input.text}
        """
        
        response = await model.ainvoke(prompt)
        result= {
            "status": "success",
            "message": response.content 
        } 
        return result
    except Exception as e:
        result = {
            "status": "error",
            "message": str(e)
            
        } 
        return result 
    
def summarize_file(user_input: Summarizermodel, request: Request):
    pass 
        