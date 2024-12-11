from src.llm_client.base import LLMClientTemplate
from src.llm_client.config import ANTHROPIC_API_KEY
from src.config import ANTHROPIC_MODEL
import aisuite as ai

class ANTHROPICClient(LLMClientTemplate):
    def _initialize_client(self):
        self._api_key = ANTHROPIC_API_KEY
        self.client = ai.Client()
        self.model = "anthropic:" + ANTHROPIC_MODEL