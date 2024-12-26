from src.llm_client.base import LLMClientTemplate
from src.llm_client.config import OPENAI_API_KEY
from src.config import OPENAI_MODEL

class OPENAIClient(LLMClientTemplate):
    def _initialize_client(self):
        self.model = "openai:" + OPENAI_MODEL