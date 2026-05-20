"""
Mortarium AI Agent powered by local Mistral Nemo.
The core intelligence that grinds raw data into precise medical answers.
Handles complex pharmacy queries using tool calling (e.g., dosage calc).
"""
from rag.routers.semantic_router import MortariumRouteType

class MortariumAgent:
    def __init__(self, llm_client, tools: dict):
        self.llm = llm_client
        self.tools = tools

    def run(self, query: str) -> str:
        """
        Executes ReAct loop with local Mistral Nemo.
        If the model returns a tool_call, execute the tool and append to context.
        """
        pass
