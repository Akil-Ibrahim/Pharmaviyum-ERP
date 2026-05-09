"""
Script to ingest documents into the vector store.
Paths updated from 'pharmacist' to 'data'.
"""
import os
from rag.pipelines.ingest import IngestionPipeline

ENV = os.getenv("RAG_ENV", "demo")

# Updated path: rag/data instead of rag/pharmacist
DOCS_PATH = f"rag/data/{ENV}/documents/"

def run_ingestion():
    pipeline = IngestionPipeline()
    pipeline.ingest_from_directory(DOCS_PATH)
    print(f"Successfully ingested documents from {DOCS_PATH}")

if __name__ == "__main__":
    run_ingestion()
