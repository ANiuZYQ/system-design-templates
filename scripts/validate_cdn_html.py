#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path


STACKS = {
    "antd5-legacy": {
        "scripts": [
            "react.production.min.js",
            "react-dom.production.min.js",
            "dayjs.min.js",
            "antd.min.js",
            "babel.min.js",
        ],
        "styles": ["antd.min.css"],
        "markers": [r'id=["\']root["\']', r"ReactDOM", r"\bantd\b", r'type=["\']text/babel["\']'],
    },
    "antd5": {
        "scripts": [
            "react.production.min.js",
            "react-dom.production.min.js",
            "dayjs.min.js",
            "antd5.min.js",
            "babel.min.js",
        ],
        "styles": ["reset.css"],
        "markers": [r'id=["\']root["\']', r"ReactDOM", r"\bantd\b", r'type=["\']text/babel["\']'],
    },
    "element-plus": {
        "scripts": ["vue.min.js", "index.full.min.js"],
        "styles": ["index.css"],
        "markers": [r'id=["\']app["\']', r"Vue\.createApp|createApp\s*\(", r"app\.use\s*\(\s*ElementPlus", r"<el-[a-z]"],
    },
}


SCRIPT_RE = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.I)
STYLE_RE = re.compile(r'<link[^>]+href=["\']([^"\']+)["\']', re.I)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


MANIFEST = json.loads(
    (Path(__file__).resolve().parents[1] / "assets" / "cdn" / "manifest.json").read_text(encoding="utf-8")
)


def local_name(reference: str) -> str:
    return Path(reference.replace("\\", "/")).name


def detect_stack(script_names: list[str]) -> str | None:
    matches = []
    if "antd5.min.js" in script_names:
        matches.append("antd5")
    if "antd.min.js" in script_names:
        matches.append("antd5-legacy")
    if "index.full.min.js" in script_names:
        matches.append("element-plus")
    if len(matches) != 1:
        return None
    return matches[0]


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    script_refs = SCRIPT_RE.findall(text)
    style_refs = STYLE_RE.findall(text)
    script_names = [local_name(ref) for ref in script_refs]
    style_names = [local_name(ref) for ref in style_refs]
    stack = detect_stack(script_names)

    if stack is None:
        return ["must reference exactly one supported component-library runtime"]

    spec = STACKS[stack]
    for ref in script_refs + style_refs:
        if ref.startswith("./cdn/") and not (path.parent / ref[2:]).is_file():
            errors.append(f"missing local asset: {ref}")

    for name in spec["scripts"]:
        matching = [ref for ref in script_refs if local_name(ref) == name]
        if not matching:
            errors.append(f"missing script: {name}")
        elif not any(ref.startswith("./cdn/") for ref in matching):
            errors.append(f"script must use local ./cdn path: {name}")
    for name in spec["styles"]:
        matching = [ref for ref in style_refs if local_name(ref) == name]
        if not matching:
            errors.append(f"missing stylesheet: {name}")
        elif not any(ref.startswith("./cdn/") for ref in matching):
            errors.append(f"stylesheet must use local ./cdn path: {name}")

    for relative in MANIFEST["stacks"][stack]["files"]:
        expected_ref = "./cdn/" + relative
        normalized_refs = [ref.replace("\\", "/") for ref in script_refs + style_refs]
        if expected_ref not in normalized_refs:
            errors.append(f"must reference bundled user-provided asset: {expected_ref}")
            continue
        asset_path = path.parent / "cdn" / relative
        if asset_path.is_file():
            expected_hash = MANIFEST["files"][relative]["sha256"]
            if sha256(asset_path) != expected_hash:
                errors.append(f"asset differs from bundled user-provided file: {expected_ref}")

    if all(name in script_names for name in spec["scripts"]):
        positions = [script_names.index(name) for name in spec["scripts"]]
        if positions != sorted(positions):
            errors.append("component-library dependency order is incorrect")

    for marker in spec["markers"]:
        if not re.search(marker, text, re.I):
            errors.append(f"runtime/component usage marker not found: {marker}")

    if stack.startswith("antd5") and re.search(r"\bTabs\b", text):
        literal_active = re.search(r"\bactiveKey\s*=\s*[\"']", text)
        if literal_active and not re.search(r"\bonChange\s*=", text):
            errors.append("Ant Design Tabs has a literal activeKey without onChange; it will not switch")
    if stack == "element-plus" and re.search(r"<el-tabs\b", text, re.I):
        if not re.search(r"<el-tabs\b[^>]*\bv-model\s*=", text, re.I):
            errors.append("Element Plus el-tabs must bind v-model to writable state")

    if any(ref.startswith(("http://", "https://", "//")) for ref in script_refs):
        errors.append("remote script found; supported runtimes must use local ./cdn assets")
    if any(ref.startswith(("http://", "https://", "//")) for ref in style_refs):
        errors.append("remote stylesheet found; supported runtimes must use local ./cdn assets")

    if errors:
        return errors
    print(f"OK {path.name}: {stack}")
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local framework/component CDN usage in generated HTML.")
    parser.add_argument("html", nargs="+")
    args = parser.parse_args()
    failed = False
    for value in args.html:
        path = Path(value).resolve()
        if not path.is_file():
            print(f"ERROR {path}: file not found")
            failed = True
            continue
        errors = validate(path)
        for error in errors:
            print(f"ERROR {path.name}: {error}")
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
