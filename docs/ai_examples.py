"""
Pharmaviyum AI API Usage Examples.

Prerequisites:
  1. FastAPI app is running: uvicorn src.pharmaviyum.main:app --reload
  2. Ollama is running with models: qwen2.5:7b, mxbai-embed-large
  3. Redis and PostgreSQL are running
  4. Install httpx: pip install httpx
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def example_sync_query():
    print("\n" + "="*60)
    print("1. SYNC QUERY WITH HALAL FILTER (Arabic, Iraq)")
    print("="*60)
    payload = {
        "query": "هل يمكنني تناول كبسولات الأموكسيسيلين؟ أنا أتبع فتوى السيد السيستاني.",
        "session_id": "test-session-1",
        "country": "IQ",
        "language": "ar",
        "halal_filter": True,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/ai/query", json=payload, timeout=60.0)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"\nAnswer:\n{data['answer']}")
        print(f"\nWarnings: {data['warnings']}")
        print(f"Safety Score: {data['safety_score']}")


async def example_stream_query():
    print("\n" + "="*60)
    print("2. STREAMING QUERY (English, Vietnam)")
    print("="*60)
    payload = {
        "query": "What are the drug interactions between Warfarin and Aspirin?",
        "country": "VN",
        "language": "en",
    }
    async with httpx.AsyncClient() as client:
        print("Streaming response:\n")
        async with client.stream("POST", f"{BASE_URL}/ai/query/stream", json=payload, timeout=60.0) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        print("\n[Stream Complete]")
                        break
                    # In a real app, you'd parse the JSON and extract the token
                    print(data, end="", flush=True)


async def example_ingestion():
    print("\n" + "="*60)
    print("3. DOCUMENT INGESTION & JOB TRACKING")
    print("="*60)
    payload = {
        "source": "/tmp/sample_drug_guideline.pdf",
        "source_type": "pdf",
        "country": "VN",
        "language": "vi",
        "extract_tables": True,
        "ocr_enabled": True,
    }
    async with httpx.AsyncClient() as client:
        # 1. Trigger ingestion
        response = await client.post(f"{BASE_URL}/ingest/documents", json=payload)
        data = response.json()
        job_id = data['job_id']
        print(f"✅ Job triggered. Job ID: {job_id}")
        
        # 2. Poll for status
        print("Polling job status...")
        for _ in range(10):
            await asyncio.sleep(2)
            status_resp = await client.get(f"{BASE_URL}/ingest/jobs/{job_id}")
            if status_resp.status_code == 200:
                job_data = status_resp.json()
                status = job_data.get('status')
                progress = job_data.get('progress_percent', 0)
                print(f"  Status: {status.upper():<12} | Progress: {progress}%")
                if status in ['completed', 'failed']:
                    break
            else:
                print("  Job not found or expired.")
                break


if __name__ == "__main__":
    print("Starting AI API Examples...")
    asyncio.run(example_sync_query())
    # Uncomment to test other examples:
    # asyncio.run(example_stream_query())
    # asyncio.run(example_ingestion())
