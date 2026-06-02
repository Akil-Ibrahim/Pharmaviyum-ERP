from typing import Dict, List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from opentelemetry import trace
from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy import text
from core.db import async_session_factory
from core.model import load_qwen_model
from data.vector_store import retriever
from core.prompts import SYSTEM_RAG, HUMAN_RAG, GRADER_SYSTEM, GRADER_HUMAN, REWRITE_SYSTEM, REWRITE_HUMAN
import structlog

logger = structlog.get_logger()
tracer = trace.get_tracer("mortarium.nodes")
llm = load_qwen_model()

class GradeResponse(BaseModel):
    is_relevant: bool = Field(description="True if document answers the query")

class RewriteResponse(BaseModel):
    rewritten_query: str = Field(description="Optimized search query")

grader_chain = ChatPromptTemplate.from_messages([("system", GRADER_SYSTEM), ("human", GRADER_HUMAN)]) | llm.with_structured_output(GradeResponse)
rewriter_chain = ChatPromptTemplate.from_messages([("system", REWRITE_SYSTEM), ("human", REWRITE_HUMAN)]) | llm.with_structured_output(RewriteResponse)

@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
def retrieve(state: Dict) -> Dict:
    with tracer.start_as_current_span("retrieve_documents"):
        docs = retriever.retrieve(state["question"], k=5)
        return {"documents": docs}

async def enrich_from_postgres(state: Dict) -> Dict:
    with tracer.start_as_current_span("enrich_db"):
        async with async_session_factory() as session:
            query = text("SELECT name, stock, price FROM products WHERE name ILIKE :q LIMIT 4")
            result = await session.execute(query, {"q": f"%{state['question']}%"})
            rows = result.fetchall()
        db_text = "\n".join(f"- {r[0]} | Stock: {r[1] or 0} | Price: {r[2] or 'N/A'}" for r in rows)
        return {"db_context": db_text or "No structured records found."}

def grade_documents(state: Dict) -> Dict:
    with tracer.start_as_current_span("grade_documents"):
        relevant = []
        for doc in state["documents"]:
            try:
                score = grader_chain.invoke({"question": state["question"], "document": doc["content"]})
                if score.is_relevant:
                    relevant.append(doc)
            except Exception as e:
                logger.warning("Grading failed", error=str(e))
        return {"documents": relevant}

async def transform_query(state: Dict) -> Dict:
    with tracer.start_as_current_span("rewrite_query"):
        try:
            result = rewriter_chain.invoke({"question": state["question"]})
            return {"question": result.rewritten_query, "retry_count": state["retry_count"] + 1}
        except Exception:
            return {"question": state["question"], "retry_count": state["retry_count"] + 1}

def generate(state: Dict) -> Dict:
    with tracer.start_as_current_span("generate_response"):
        vector_docs = "\n".join(d["content"] for d in state["documents"]) if state["documents"] else "No vector matches."
        db_context = state.get("db_context", "No database matches.")
        prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_RAG), ("human", HUMAN_RAG)])
        chain = prompt | llm
        response = chain.invoke({"question": state["question"], "vector_docs": vector_docs, "db_context": db_context})
        return {"generation": response.content.strip()}
