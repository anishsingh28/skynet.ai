from pydantic import BaseModel

class Summarizermodel(BaseModel):
    text: str = None
    file: str = None
    
    