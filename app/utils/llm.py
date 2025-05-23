from langchain_openai import ChatOpenAI
from config.settings import get_settings
  



settings = get_settings()

class LLM:
    def __init__(self):
        self.model = settings.llm.model
        self.endpoint = settings.llm.endpoint
        self.token = settings.llm.token
        print(self.token) 
        self.openai_model = ChatOpenAI(
            api_key=self.token, 
            model=self.model, 
            base_url=self.endpoint, 
            temperature=settings.llm.temperature
        )
        
    def get_openai_model(self):
        return self.openai_model