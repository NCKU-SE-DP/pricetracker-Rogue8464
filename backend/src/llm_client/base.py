import abc
from src.crawler.exceptions import DomainMismatchException
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str = Field(..., example="user", description="The role of the sender (system, user, assistant)")
    content: str = Field(..., example="Hello, how can I help you?", description="The content of the message")

class LLMClientBase(metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def sum_up_news() -> dict:
        
        return NotImplemented
    
    @abc.abstractmethod
    def sum_up_news() -> str:
        
        return NotImplemented
    
    @abc.abstractmethod
    def evaluate_relevance() -> str:
        
        return NotImplemented