from typing import Annotated, List, Optional
from operator import add
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

class GraphState(TypedDict):
    question: str
    generation: Optional[str]
    documents: List[str]
    db_context: Optional[str]
    metadata: dict
    retry_count: int
    chat_history: Annotated[List[BaseMessage], add]
