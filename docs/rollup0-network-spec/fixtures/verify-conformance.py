#!/usr/bin/env python3
"""Generate or verify the Rollup0-v0 conformance corpus and Python fixtures."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import unicodedata
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import unquote, urlsplit

from conformance_vectors import fixture_document


FIXTURES = Path(__file__).resolve().parent
SPEC = FIXTURES.parent
REPOSITORY = SPEC.parents[1]
CORPUS = FIXTURES / "conformance-vectors.json"
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
ATX_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
REQUIRED_PACKAGES = {
    "eth-abi": "5.2.0",
    "eth-hash": "0.7.1",
    "eth-keys": "0.7.0",
    "eth-utils": "5.3.1",
    "pycryptodome": "3.23.0",
    "rlp": "4.1.0",
}


def check_versions() -> None:
    errors: list[str] = []
    for package, expected in REQUIRED_PACKAGES.items():
        try:
            actual = version(package)
        except PackageNotFoundError:
            errors.append(f"{package} is missing; expected {expected}")
            continue
        if actual != expected:
            errors.append(f"{package}=={actual}; expected {package}=={expected}")
    if errors:
        raise RuntimeError(
            "conformance environment mismatch:\n  - "
            + "\n  - ".join(errors)
            + "\nInstall fixtures/conformance-requirements.txt in an isolated environment."
        )


def canonical_json() -> str:
    return json.dumps(fixture_document(), indent=2, sort_keys=True) + "\n"


def run_fixture(name: str) -> None:
    result = subprocess.run([sys.executable, str(FIXTURES / name)], check=False)
    if result.returncode:
        raise RuntimeError(f"{name} failed with exit code {result.returncode}")
    print(f"{name}: OK")


def github_slug(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"!?\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = value.replace("`", "").lower()
    value = "".join(
        character
        for character in value
        if not unicodedata.category(character).startswith("P") or character in "-_"
    )
    return re.sub(r"\s+", "-", value.strip())


def markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    occurrences: dict[str, int] = {}
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = ATX_HEADING.match(line)
        if not match:
            continue
        base = github_slug(match.group(1))
        occurrence = occurrences.get(base, 0)
        occurrences[base] = occurrence + 1
        anchors.add(base if occurrence == 0 else f"{base}-{occurrence}")
    return anchors


def check_markdown_links() -> None:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    for markdown in sorted(SPEC.glob("*.md")):
        source = markdown.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(source):
            raw = match.group(1).strip()
            if raw.startswith("<") and raw.endswith(">"):
                raw = raw[1:-1]
            raw = raw.split(maxsplit=1)[0]
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc:
                continue

            target = markdown if not parsed.path else (markdown.parent / unquote(parsed.path)).resolve()
            line = source.count("\n", 0, match.start()) + 1
            label = f"{markdown.relative_to(REPOSITORY)}:{line}"
            if not target.exists():
                errors.append(f"{label}: missing {unquote(parsed.path)}")
                continue

            fragment = unquote(parsed.fragment)
            if fragment and target.suffix.lower() == ".md":
                anchors = anchor_cache.setdefault(target, markdown_anchors(target))
                if fragment not in anchors:
                    errors.append(f"{label}: missing #{fragment} in {target.relative_to(REPOSITORY)}")

    if errors:
        raise RuntimeError("broken Rollup0 Markdown links:\n  - " + "\n  - ".join(errors))
    print("Rollup0 Markdown targets and fragments: OK")


def check_sources() -> None:
    forbidden = {
        "fe7bf6644dacd64bb41707feae2d84699a97afb4",
        "0xb674ac54ef248bfe921085a167b225ed55b29a26f4d16538d568a88244d7c4af",
        "0x532f0839",
        "0x9f149e1b",
        "753bf6645d28553aff39043d4aec89b1fb39185c82ddcd2bb6d8216cc3683f7c",
    }
    for path in (
        FIXTURES / "conformance_vectors.py",
        FIXTURES / "conformance-vectors.json",
        FIXTURES / "wire-vectors.s.sol",
        FIXTURES / "system-tx-vector.rs",
    ):
        text = path.read_text(encoding="utf-8")
        stale = sorted(value for value in forbidden if value in text)
        if stale:
            raise RuntimeError(f"{path.name} contains obsolete values: {stale}")
    print("Rollup0 source/version boundary: OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--skip-versions", action="store_true")
    args = parser.parse_args()

    if not args.skip_versions:
        check_versions()

    expected = canonical_json()
    if args.write:
        CORPUS.write_text(expected, encoding="utf-8")
        print(f"wrote {CORPUS}")
        return
    if not CORPUS.exists() or CORPUS.read_text(encoding="utf-8") != expected:
        raise RuntimeError("conformance-vectors.json drift; run with --write")
    print("conformance-vectors.json: OK")

    for name in (
        "da-rlp-fixture.py",
        "da-strict-fixture.py",
        "system-tx-fixture.py",
        "timing-header-fixture.py",
        "genesis-hash-fixture.py",
    ):
        run_fixture(name)
    check_markdown_links()
    check_sources()
    print("all Rollup0 conformance checks passed")


if __name__ == "__main__":
    main()
