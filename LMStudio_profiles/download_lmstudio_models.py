#!/usr/bin/env python3
"""
Robust LM Studio model downloader using Hugging Face.

This does NOT rely on OpenWebUI or Ollama. It downloads specified model
artifacts (e.g., GGUF) to a local directory and verifies completion.

Usage:
  python LMStudio_profiles/download_lmstudio_models.py \
    --map-file LMStudio_profiles/models_map.json \
    --out-dir models \
    [--hf-token <HF_TOKEN>] [--force]

Mapping file format (JSON):
[
  {
    "name": "Meta-Llama-3-8B-Instruct",
    "repo_id": "TheBloke/Meta-Llama-3-8B-Instruct-GGUF",
    "allow_patterns": ["*Q4*gguf"],
    "sha256": null
  }
]

Note: Some repos require license acceptance (HF token). Set via --hf-token or HF_TOKEN env var.
"""

import os
import json
import argparse
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from huggingface_hub import snapshot_download, hf_hub_download
except ImportError:
    raise SystemExit("Install huggingface_hub: pip install huggingface_hub")


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def download_entry(entry: Dict[str, Any], out_dir: Path, token: Optional[str], force: bool) -> List[Path]:
    name = entry.get('name')
    repo_id = entry.get('repo_id')
    allow_patterns = entry.get('allow_patterns') or []
    expected_sha256 = entry.get('sha256')

    if not repo_id:
        print(f"❌ Missing repo_id for entry: {name}")
        return []

    print(f"📥 Downloading {name or repo_id} ...")

    # snapshot_download returns the local folder path; we filter matched files
    local_dir = snapshot_download(
        repo_id=repo_id,
        allow_patterns=allow_patterns if allow_patterns else None,
        local_dir=out_dir,
        local_dir_use_symlinks=False,
        token=token,
        tqdm_class=None,
        resume_download=True,
    )

    downloaded_paths: List[Path] = []
    base = Path(local_dir)
    if allow_patterns:
        # Collect only files that match patterns
        for pat in allow_patterns:
            downloaded_paths.extend(base.rglob(pat))
    else:
        downloaded_paths.extend([p for p in base.rglob('*') if p.is_file()])

    if not downloaded_paths:
        print(f"❌ No files matched for {name or repo_id}. Check allow_patterns.")
        return []

    # Verify integrity if sha256 provided and single-file scenario
    if expected_sha256 and len(downloaded_paths) == 1:
        actual = sha256sum(downloaded_paths[0])
        if actual.lower() != expected_sha256.lower():
            print(f"❌ SHA256 mismatch for {downloaded_paths[0].name}: {actual} != {expected_sha256}")
            return []

    for p in downloaded_paths:
        print(f"   ✅ {p.relative_to(out_dir)} ({p.stat().st_size/1e6:.1f} MB)")

    return downloaded_paths


def main():
    ap = argparse.ArgumentParser(description='Download models for LM Studio (via Hugging Face)')
    ap.add_argument('--map-file', required=True, help='JSON mapping file of models to download')
    ap.add_argument('--out-dir', default='models', help='Output directory for downloaded weights')
    ap.add_argument('--hf-token', default=os.getenv('HF_TOKEN'), help='Hugging Face token (if required)')
    ap.add_argument('--force', action='store_true', help='Re-download even if files exist')
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.map_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    if not isinstance(mapping, list):
        raise SystemExit('Map file must be a JSON list of entries')

    total_files = 0
    for entry in mapping:
        files = download_entry(entry, out_dir, token=args.hf_token, force=args.force)
        total_files += len(files)

    print(f"\n📊 Finished. Downloaded/verified files: {total_files}")
    print("Next: In LM Studio, use 'Add local model' to load GGUF from the output directory.")


if __name__ == '__main__':
    main()


