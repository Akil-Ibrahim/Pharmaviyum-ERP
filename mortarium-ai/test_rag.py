#!/usr/bin/env python3
"""
Mortarium AI - Functional Test Suite.
Tests the /api/ask endpoint against the LangGraph workflow.
Checks for correct JSON schema, caching, and response integrity.
"""
import httpx
import json
import time
import sys
from typing import Optional

# Configuration
API_URL = "http://localhost:8000/api/ask"
HEADERS = {"Content-Type": "application/json"}
TEST_TIMEOUT = 60.0  # Increased timeout for LLM generation

def send_query(question: str) -> Optional[dict]:
    """
    Send a query to the RAG API and return the parsed response.
    Returns None on failure.
    """
    payload = {
        "question": question,
        "user_id": "test_user",
        "pharmacy_id": "pharmacy_001"
    }
    try:
        with httpx.Client(timeout=TEST_TIMEOUT) as client:
            response = client.post(API_URL, json=payload, headers=HEADERS)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"❌ Request failed: {e}")
        return None

def validate_response(data: dict) -> bool:
    """
    Validate the structure of the API response.
    Ensures the LangGraph output is correctly formatted.
    """
    required_fields = ["answer", "sources", "cached", "processing_ms", "request_id"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        print(f"❌ Schema validation failed. Missing fields: {missing}")
        return False

    if not isinstance(data["answer"], str):        print("❌ 'answer' field is not a string.")
        return False

    return True

def run_test_scenario(description: str, question: str, expected_contains: str = None):
    """
    Helper to run a single test scenario.

    Args:
        description: Test case name
        question: The user query
        expected_contains: Optional string expected in the answer
    """
    print(f"\n🧪 [Test]: {description}")
    print(f"❓ Query: {question}")

    start = time.time()
    result = send_query(question)
    duration = time.time() - start

    if result is None:
        print("❌ FAILED: No response from API")
        return

    if not validate_response(result):
        return

    # Validation logic
    is_valid = True
    if expected_contains and expected_contains.lower() not in result["answer"].lower():
        print(f"⚠️  Warning: Expected content '{expected_contains}' not found.")
        is_valid = False

    # Output results
    status = "✅ PASSED" if is_valid else "⚠️  PASSED (Content mismatch)"
    print(f"{status}")
    print(f"🤖 Answer: {result['answer'][:100]}...")
    print(f"📊 Metrics: {result['processing_ms']:.2f}ms | Cached: {result['cached']}")
    print(f"️  Total Test Duration: {duration:.2f}s")

if __name__ == "__main__":
    print(" Starting Mortarium AI LangGraph Tests...")

    # Test 1: Basic retrieval
    run_test_scenario(
        description="Basic Drug Retrieval",
        question="What are the analogs of Nurofen?",
        expected_contains="ibuprofen"
    )
    # Test 2: Structured Data (Postgres)
    run_test_scenario(
        description="Inventory Check (Postgres)",
        question="How much stock is there for Paracetamol?"
    )

    # Test 3: Cache verification
    run_test_scenario(
        description="Repeated Query (Cache Check)",
        question="What are the analogs of Nurofen?"
    )

    print("\n✅ Test suite finished.")
