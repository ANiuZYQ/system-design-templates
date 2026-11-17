#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_node() -> str | None:
    configured = os.environ.get("CODEX_NODE_PATH")
    if configured and Path(configured).is_file():
        return configured

    executable = "node.exe" if os.name == "nt" else "node"
    runtime_root = Path.home() / ".cache" / "codex-runtimes"
    candidates = sorted(
        runtime_root.glob(f"*/dependencies/node/bin/{executable}"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ) if runtime_root.is_dir() else []
    if candidates:
        return str(candidates[0])

    return shutil.which("node")


def main() -> int:
    node = find_node()
    if not node:
        print(
            "ERROR: Node.js is required for inline JavaScript/JSX syntax validation. "
            "Set CODEX_NODE_PATH or install Node.js.",
            file=sys.stderr,
        )
        return 2

    validator = Path(__file__).with_name("validate_html_syntax.js")
    if not validator.is_file():
        print(f"ERROR: validator helper not found: {validator}", file=sys.stderr)
        return 2

    completed = subprocess.run([node, str(validator), *sys.argv[1:]], check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
