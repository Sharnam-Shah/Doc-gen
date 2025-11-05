import argparse
import os
import shutil
from pathlib import Path
from typing import List

from config import TEMPLATE_DIR


def find_text_files(root: str) -> List[Path]:
    p = Path(root)
    if not p.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    return [path for path in p.rglob("*.txt")]


def copy_as_templates(src_files: List[Path], limit: int | None = None) -> int:
    Path(TEMPLATE_DIR).mkdir(parents=True, exist_ok=True)
    count = 0
    for i, src in enumerate(sorted(src_files)):
        if limit is not None and count >= limit:
            break
        # Produce a normalized destination filename
        # Keep original stem, but ensure filesystem-safe
        stem = src.stem.lower().replace(" ", "_")
        safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in stem)
        dest = Path(TEMPLATE_DIR) / f"ext_{i:05d}_{safe}.txt"
        # Avoid overwriting existing identical content
        if not dest.exists():
            shutil.copyfile(src, dest)
            count += 1
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import external .txt contracts as templates")
    parser.add_argument("--path", required=True, help="Root folder containing .txt files (e.g. CUAD full_contract_txt)")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on number of files to import")
    args = parser.parse_args()

    files = find_text_files(args.path)
    if not files:
        raise SystemExit("No .txt files found under the provided path.")

    added = copy_as_templates(files, args.limit)
    print(f"Imported {added} file(s) into {TEMPLATE_DIR}")


