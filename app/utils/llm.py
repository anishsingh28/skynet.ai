from langchain_openai import ChatOpenAI   

from dotenv import load_dotenv
import os
load_dotenv()

class LLM:
    def __init__(self):
        self.model = os.getenv("LLM_MODEL")
        self.endpoint = os.getenv("LLM_ENDPOINT")
        self.token = os.getenv("GITHUB_TOKEN")
        os.environ["GITHUB_TOKEN"] = self.token
        
        self.openai_model = ChatOpenAI(api_key=self.token, model=self.model, base_url=self.endpoint, temperature=1)
        
    def get_openai_model(self):
        return self.openai_model