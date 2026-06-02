#!/usr/bin/env python3
"""Install a local Qwen GGUF model for developer use.

This script downloads a Qwen model from a direct URL or Hugging Face repo and saves it to a local folder.
It does not modify `mortarium-ai` files.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urljoin


def download_file(url: str, dest_path: Path, headers: dict | None = None) -> None:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=360) as resp:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as out:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    out.write(chunk)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code} downloading {url}: {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL error downloading {url}: {e.reason}")


def resolve_hf_url(repo: str, filename: str) -> str:
    repo = repo.strip().strip("/")
    if not filename:
        raise ValueError("filename is required for Hugging Face download")
    return urljoin(f"https://huggingface.co/{repo}/resolve/main/", filename)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download a Qwen GGUF model for local developer use.")
    parser.add_argument("--dest", default="./models/qwen3", help="Destination directory for the downloaded model")
    parser.add_argument("--source-url", help="Direct URL to the GGUF model file")
    parser.add_argument("--hf-repo", help="Hugging Face repo name, e.g. 'Qwen/Qwen-3.6' or 'Qwen/Qwen-3.7'")
    parser.add_argument("--filename", help="Model filename inside the Hugging Face repo or direct URL")
    parser.add_argument("--hf-token", help="Optional Hugging Face token for private/download-protected repos")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing file if it exists")
    args = parser.parse_args()

    if not args.source_url and not args.hf_repo:
        parser.error("Either --source-url or --hf-repo must be provided")

    if args.hf_repo and not args.filename:
        parser.error("--filename is required when using --hf-repo")

    dest_dir = Path(args.dest).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    if args.source_url:
        url = args.source_url
        filename = args.filename or Path(url).name
    else:
        url = resolve_hf_url(args.hf_repo, args.filename)
        filename = args.filename

    dest_path = dest_dir / filename
    if dest_path.exists() and not args.overwrite:
        print(f"File already exists: {dest_path}")
        print("Use --overwrite to replace it.")
        return 0

    headers = {}
    if args.hf_token:
        headers["Authorization"] = f"Bearer {args.hf_token}"

    print(f"Downloading model from: {url}")
    print(f"Saving to: {dest_path}")
    download_file(url, dest_path, headers=headers)
    print("Download complete.")
    print("Next: mount the model folder into Mortarium AI and set MODEL_PATH to the downloaded file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
