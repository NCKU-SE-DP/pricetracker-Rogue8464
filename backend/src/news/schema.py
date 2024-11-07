from pydantic import BaseModel

class NewsSumaryRequestSchema(BaseModel):
    content: str

class PromptRequest(BaseModel):
    prompt: str