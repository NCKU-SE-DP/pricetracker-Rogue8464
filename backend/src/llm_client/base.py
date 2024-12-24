import abc
import json
import aisuite as ai
from src.crawler.exceptions import DomainMismatchException
from pydantic import BaseModel, Field
from src.logger_config import logger

class Message(BaseModel):
    role: str = Field(..., example="user", description="The role of the sender (system, user, assistant)")
    content: str = Field(..., example="Hello, how can I help you?", description="The content of the message")

class LLMClientBase(metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def sum_up_news() -> dict:
        
        return NotImplemented
    
    @abc.abstractmethod
    def extract_keywords() -> str:
        
        return NotImplemented
    
    @abc.abstractmethod
    def evaluate_relevance() -> str:
        
        return NotImplemented

class LLMClientTemplate(LLMClientBase,abc.ABC):
    def __init__(self):
        self.client = ai.Client()
        self.model = None
        self._initialize_client()

    @abc.abstractmethod
    def _initialize_client(self):        
        pass

    def _perform_request(self,message_content) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message_content,
            )
            result = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error happened during perfroming LLM request:{e}",exc_info=True)
            raise
        return result

    def _create_message_content(self,system_role,user_content):
        system_message = Message(role="system", content=system_role)
        user_message = Message(role="user", content=user_content)
        message_content = [system_message.dict(), user_message.dict()]
        return message_content

    def sum_up_news(self,content) -> dict:
        response = {}
        system_role = "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})"
        message_content = self._create_message_content(system_role,content)
        result = self._perform_request(message_content)
        if result:
            try:
                result = json.loads(result)
                response["summary"] = result['影響']
                response["reason"] = result['原因']
            except Exception as e:
                logger.error(f"Error happened during processing news summary:{e}",exc_info=True)
                raise
        return response
    
    def extract_keywords(self,prompt) -> str:
        system_role = "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)"
        message_content = self._create_message_content(system_role,prompt)
        keywords = self._perform_request(message_content)
        return keywords
    
    def evaluate_relevance(self,title) -> str:
        system_role = "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)"
        message_content = self._create_message_content(system_role,title)
        relevance = self._perform_request(message_content)
        return relevance