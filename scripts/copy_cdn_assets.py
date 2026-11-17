#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy the user-provided UI runtime bundled with this skill.")
    parser.add_argument("--stack", required=True, help="antd5, antd5-legacy, or element-plus")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--skill-root")
    args = parser.parse_args()

    skill_root = Path(args.skill_root).resolve() if args.skill_root else Path(__file__).resolve().parents[1]
    source_root = skill_root / "assets" / "cdn"
    manifest_path = source_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_root = Path(args.output_dir).resolve() / "cdn"

    if args.stack not in manifest["stacks"]:
        choices = ", ".join(sorted(manifest["stacks"]))
        raise SystemExit(f"Unknown stack {args.stack!r}; choose one of: {choices}")

    if not source_root.is_dir():
        raise SystemExit(f"CDN asset directory not found: {source_root}")

    for relative in manifest["stacks"][args.stack]["files"]:
        source = source_root / relative
        target = output_root / relative
        if not source.is_file():
            raise SystemExit(f"Required CDN asset not found: {source}")
        expected = manifest["files"][relative]["sha256"]
        if sha256(source) != expected:
            raise SystemExit(f"Bundled CDN asset hash mismatch: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if sha256(target) != expected:
            raise SystemExit(f"Copied CDN asset hash mismatch: {target}")
        print(f"copied {relative}")

    print(f"ready: {args.stack} -> {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
