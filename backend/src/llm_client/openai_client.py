from src.llm_client.base import LLMClientTemplate
from src.llm_client.config import OPENAI_API_KEY
from src.config import OPENAI_MODEL
import aisuite as ai

class OPENAIClient(LLMClientTemplate):
    def _initialize_client(self):
        self._api_key = OPENAI_API_KEY
        self.client = ai.Client()
        self.model = "openai:" + OPENAI_MODEL