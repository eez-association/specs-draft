#!/usr/bin/env python3
"""Verify the split EEZ and Rollup0 companion conformance suites."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import unquote, urlsplit

from conformance_vectors import fixture_document


ROOT = Path(__file__).resolve().parents[1]
COMPANION = ROOT / "companion-docs"
CORPUS = COMPANION / "fixtures/conformance-vectors.json"
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
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
            + "\nInstall companion-docs/conformance-requirements.txt in an isolated environment."
        )


def canonical_json() -> str:
    return json.dumps(fixture_document(), indent=2, sort_keys=True) + "\n"


def check_corpus(write: bool) -> None:
    expected = canonical_json()
    if write:
        CORPUS.parent.mkdir(parents=True, exist_ok=True)
        CORPUS.write_text(expected, encoding="utf-8")
        print(f"wrote {CORPUS.relative_to(ROOT)}")
        return
    if not CORPUS.exists():
        raise RuntimeError(
            f"{CORPUS.relative_to(ROOT)} is missing; run this verifier with --write"
        )
    actual = CORPUS.read_text(encoding="utf-8")
    if actual != expected:
        raise RuntimeError(
            f"{CORPUS.relative_to(ROOT)} has drifted; run this verifier with --write"
        )
    print("generated conformance corpus: OK")


def run_fixture(relative: str) -> None:
    command = [sys.executable, str(ROOT / relative)]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode:
        raise RuntimeError(f"{relative} failed with exit code {completed.returncode}")
    print(f"{relative}: OK")


def check_markdown_links() -> None:
    errors: list[str] = []
    for markdown in sorted(COMPANION.glob("*.md")):
        text = markdown.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            raw = match.group(1).strip()
            if raw.startswith("<") and raw.endswith(">"):
                raw = raw[1:-1]
            raw = raw.split(maxsplit=1)[0]
            parsed = urlsplit(raw)
            if parsed.scheme or raw.startswith("#"):
                continue
            target_text = unquote(parsed.path)
            if not target_text:
                continue
            target = (markdown.parent / target_text).resolve()
            if not target.exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(
                    f"{markdown.relative_to(ROOT)}:{line}: missing {target_text}"
                )
    if errors:
        raise RuntimeError("broken companion Markdown links:\n  - " + "\n  - ".join(errors))
    print("companion Markdown links: OK")


def check_stale_active_claims() -> None:
    forbidden = {
        "fe7bf6644dacd64bb41707feae2d84699a97afb4": "obsolete contract pin",
        "forge-able value-minting": "obsolete mint characterization",
    }
    errors: list[str] = []
    active_files = [
        COMPANION / "README.md",
        COMPANION / "conformance_vectors.py",
        COMPANION / "blob-da-spec.md",
    ]
    for path in active_files:
        text = path.read_text(encoding="utf-8")
        for needle, description in forbidden.items():
            if needle in text:
                errors.append(f"{path.relative_to(ROOT)}: {description}: {needle}")
    if errors:
        raise RuntimeError("stale active claims:\n  - " + "\n  - ".join(errors))
    print("active conformance provenance: OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="regenerate companion-docs/fixtures/conformance-vectors.json",
    )
    parser.add_argument(
        "--skip-versions",
        action="store_true",
        help="skip exact Python package-version checks",
    )
    args = parser.parse_args()

    if not args.skip_versions:
        check_versions()
    check_corpus(args.write)
    if args.write:
        return

    for fixture in (
        "companion-docs/da-rlp-fixture.py",
        "companion-docs/system-tx-fixture.py",
        "companion-docs/timing-header-fixture.py",
        "companion-docs/genesis-hash-fixture.py",
    ):
        run_fixture(fixture)
    check_markdown_links()
    check_stale_active_claims()
    print("all companion conformance checks passed")


if __name__ == "__main__":
    main()
