from src.llm_client.base import LLMClientTemplate
from src.llm_client.config import ANTHROPIC_API_KEY
from src.config import ANTHROPIC_MODEL

class ANTHROPICClient(LLMClientTemplate):
    def _initialize_client(self):
        self.model = "anthropic:" + ANTHROPIC_MODEL