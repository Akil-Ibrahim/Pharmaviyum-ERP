#!/usr/bin/env python3
"""Simple CLI client for working with local Mortarium AI (Qwen-based).

Example:
  python tools/qwen_dev_agent.py --question "Explain the function in src/..."
"""
import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import ssl

# Create unverified SSL context to avoid cert issues in local dev
_SSL_CTX = ssl.create_default_context()


def ask_remote_via_url(url: str, question: str, user_id: str | None = None, timeout: int = 15) -> dict | None:
    payload = {"question": question}
    if user_id:
        payload["user_id"] = user_id
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return json.load(resp)
    except HTTPError as e:
        # Treat 4xx billing/auth errors as signal to fallback
        if e.code in (401, 402, 403):
            return None
        raise
    except URLError:
        return None


def ask_local(url: str, question: str, user_id: str | None = None) -> dict:
    # Local mortarium endpoint expects same payload
    return ask_remote_via_url(url, question, user_id)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--local-url", default="http://localhost:8000/api/ask", help="Mortarium AI endpoint")
    p.add_argument("--remote-url", default=os.getenv("REMOTE_API_URL"), help="Optional remote LLM API endpoint")
    p.add_argument("--question", required=True, help="Question or prompt for the agent")
    p.add_argument("--user", default=None, help="user_id for context")
    args = p.parse_args()

    # Try remote provider first if configured
    resp = None
    if args.remote_url:
        try:
            resp = ask_remote_via_url(args.remote_url, args.question, args.user)
            if resp is None:
                print("Remote provider returned authorization/payment error — switching to local.", file=sys.stderr)
        except Exception as e:
            print(f"Error communicating with remote provider: {e}", file=sys.stderr)
            resp = None

    # If remote not set or failed, use OPENAI if available
    if resp is None and os.getenv("OPENAI_API_KEY"):
        # Try a basic OpenAI Chat API call
        try:
            openai_resp = ask_openai(os.getenv("OPENAI_API_KEY"), args.question)
            resp = {"answer": openai_resp}
        except Exception as e:
            print(f"OpenAI request failed: {e}", file=sys.stderr)
            resp = None

    # Finally, fallback to local Mortarium AI
    if resp is None:
        try:
            resp = ask_local(args.local_url, args.question, args.user)
        except Exception as e:
            print(f"Error communicating with local Mortarium AI: {e}", file=sys.stderr)
            sys.exit(2)

    # Print agent response in readable format
    print("--- Agent Response ---")
    print(resp.get("answer", json.dumps(resp, ensure_ascii=False, indent=2)))
    if resp.get("sources"):
        print("\n--- Sources ---")
        for s in resp["sources"]:
            print(json.dumps(s, ensure_ascii=False))


def ask_openai(api_key: str, question: str) -> str:
    """Minimal OpenAI ChatCompletions call using REST API. Returns text or raises."""
    import urllib.request, urllib.error

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": question}],
        "max_tokens": 800,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=15) as resp:
            j = json.load(resp)
            # Extract text from response
            return j["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        if e.code in (401, 402, 403):
            raise RuntimeError("OpenAI billing/auth error")
        raise


if __name__ == "__main__":
    main()
