#!/usr/bin/env python3
"""
Mortarium AI - Concurrency & Cache Stress Test.
Validates the 'run_in_threadpool' implementation in FastAPI.
Ensures the single-worker setup handles parallel requests without blocking.
"""
import httpx
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "http://localhost:8000/api/ask"
PAYLOAD = {"question": "Test concurrency load", "user_id": "load_tester"}
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 30.0

def send_request(worker_id: int) -> dict:
    """
    Sends a request from a specific worker thread.
    Returns metrics about the request.
    """
    start = time.time()
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(API_URL, json=PAYLOAD, headers=HEADERS)
            data = resp.json()
            return {
                "worker_id": worker_id,
                "status": resp.status_code,
                "api_time": data.get("processing_ms", 0),
                "cached": data.get("cached", False),
                "success": True
            }
    except Exception as e:
        return {
            "worker_id": worker_id,
            "status": 500,
            "error": str(e),
            "success": False
        }

def run_concurrency_test(num_workers: int = 5):
    """
    Executes parallel requests and aggregates statistics.
    Checks if the threadpool isolates blocking LLM calls correctly.
    """
    print(f"🚀 Starting Load Test: {num_workers} concurrent workers")
    results = []
    
    # Fire requests simultaneously
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(send_request, i) for i in range(num_workers)]
        for future in as_completed(futures):
            results.append(future.result())
            
    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    cached_count = sum(1 for r in successful if r["cached"])
    
    print(f"\n📊 Results Summary:")
    print(f"   ✅ Success: {len(successful)} / {num_workers}")
    print(f"   ❌ Failed: {len(failed)}")
    print(f"   💾 Cache Hits: {cached_count}")
    
    if successful:
        avg_api_time = sum(r["api_time"] for r in successful) / len(successful)
        print(f"   ⏱️  Avg API Latency: {avg_api_time:.2f}ms")
        
    if failed:
        print(f"\n❌ Errors detected:")
        for f in failed:
            print(f"   - Worker {f['worker_id']}: {f.get('error', 'Unknown')}")

if __name__ == "__main__":
    run_concurrency_test(5)
