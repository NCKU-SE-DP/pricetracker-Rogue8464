import abc
from src.crawler.exceptions import DomainMismatchException
from pydantic import BaseModel, Field

class MessagePassingInterfaceExample(BaseModel):
    role: str = Field(
        default=...,
        example="example",
        description="description"
    )
    content: str = Field(
        default=...,
        example="example",
        description="description"
    )

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