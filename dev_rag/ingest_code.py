"""
LangChain-based ingestion script for the PharmaViyum codebase.
Parses Python and TypeScript code using Language-specific splitters.
"""
import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    Language,
)

CODE_DIRS = [
    "./src/pharmaviyum",  # Python Backend
    "./frontend/src",     # Next.js Frontend
    "./rag",              # Mortarium AI
]

def ingest_codebase(vectorstore):
    """Loads, splits, and indexes the codebase into the vector store."""
    all_docs = []
    
    py_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON, chunk_size=1500, chunk_overlap=150
    )
    js_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.JS, chunk_size=1500, chunk_overlap=150
    )

    for code_dir in CODE_DIRS:
        if not os.path.exists(code_dir): continue
            
        py_docs = DirectoryLoader(code_dir, glob="**/*.py", loader_cls=TextLoader).load_and_split(py_splitter)
        js_docs = DirectoryLoader(code_dir, glob="**/*.{ts,tsx}", loader_cls=TextLoader).load_and_split(js_splitter)
        text_docs = DirectoryLoader(code_dir, glob="**/*.{md,yaml,yml}", loader_cls=TextLoader).load_and_split(
            RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        )
        all_docs.extend(py_docs + js_docs + text_docs)

    for doc in all_docs:
        doc.metadata["source_type"] = "codebase"

    print(f"Indexing {len(all_docs)} code chunks into custom RAG...")
    vectorstore.add_documents(all_docs)
