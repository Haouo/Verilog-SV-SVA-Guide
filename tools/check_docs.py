#!/usr/bin/env python3
"""Repository-local checks for the mirrored Markdown guide."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
ALLOWED_FENCE_LABELS = {"verilog", "systemverilog", "text"}


@dataclass
class Finding:
    path: Path
    line: int | None
    message: str

    def format(self) -> str:
        rel = self.path.relative_to(ROOT)
        if self.line is None:
            return f"{rel}: {self.message}"
        return f"{rel}:{self.line}: {self.message}"


def markdown_files() -> list[Path]:
    ignored_parts = {".git", "PDFs"}
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(part in ignored_parts for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return sorted(files)


def is_external_link(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:"))


def strip_anchor_and_title(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = target.split("#", 1)[0]
    return target


def check_links(files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in LINK_RE.finditer(line):
                raw_target = match.group(1)
                target = strip_anchor_and_title(raw_target)
                if not target or is_external_link(target):
                    continue
                if not (path.parent / target).resolve().exists():
                    findings.append(
                        Finding(path, lineno, f"missing Markdown link target: {raw_target}")
                    )
    return findings


def check_fences(files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        in_fence = False
        opener_line: int | None = None
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.startswith("```"):
                continue

            if in_fence:
                in_fence = False
                opener_line = None
                continue

            label = line.removeprefix("```").strip()
            if label not in ALLOWED_FENCE_LABELS:
                allowed = ", ".join(sorted(ALLOWED_FENCE_LABELS))
                findings.append(
                    Finding(path, lineno, f"opening code fence must use one of: {allowed}")
                )
            in_fence = True
            opener_line = lineno

        if in_fence:
            findings.append(Finding(path, opener_line, "unclosed code fence"))
    return findings


def mirrored_relpaths(language: str) -> set[Path]:
    return {path.relative_to(ROOT / language) for path in (ROOT / language).rglob("*.md")}


def heading_shape(path: Path) -> list[int]:
    levels: list[int] = []
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.startswith("#"):
            continue
        marks = len(line) - len(line.lstrip("#"))
        if marks and len(line) > marks and line[marks] == " ":
            levels.append(marks)
    return levels


def check_mirror() -> list[Finding]:
    findings: list[Finding] = []
    en_files = mirrored_relpaths("en")
    zh_files = mirrored_relpaths("zh-TW")

    for rel in sorted(en_files - zh_files):
        findings.append(Finding(ROOT / "en" / rel, None, "missing zh-TW mirror file"))
    for rel in sorted(zh_files - en_files):
        findings.append(Finding(ROOT / "zh-TW" / rel, None, "missing en mirror file"))

    for rel in sorted(en_files & zh_files):
        en_shape = heading_shape(ROOT / "en" / rel)
        zh_shape = heading_shape(ROOT / "zh-TW" / rel)
        if en_shape != zh_shape:
            findings.append(
                Finding(
                    ROOT / "en" / rel,
                    None,
                    f"heading level shape differs from zh-TW mirror: {en_shape} != {zh_shape}",
                )
            )
    return findings


def chapter_files(language: str) -> list[Path]:
    base = ROOT / language
    files = [base / "00-introduction.md"]
    files.extend(sorted((base / "part1-verilog").glob("*.md")))
    files.extend(sorted((base / "part2-systemverilog").glob("*.md")))
    files.extend(sorted((base / "part3-sva").glob("*.md")))
    return files


def check_chapter_shape() -> list[Finding]:
    findings: list[Finding] = []
    for path in chapter_files("en"):
        text = path.read_text(encoding="utf-8")
        if "> **Design intent.**" not in text:
            findings.append(Finding(path, None, "missing English design-intent callout"))
    for path in chapter_files("zh-TW"):
        text = path.read_text(encoding="utf-8")
        if "> **設計意圖。**" not in text:
            findings.append(Finding(path, None, "missing Traditional Chinese design-intent callout"))
    return findings


def main() -> int:
    files = markdown_files()
    findings: list[Finding] = []
    findings.extend(check_links(files))
    findings.extend(check_fences(files))
    findings.extend(check_mirror())
    findings.extend(check_chapter_shape())

    if findings:
        print("Documentation checks failed:")
        for finding in findings:
            print(f"- {finding.format()}")
        return 1

    print(f"Documentation checks passed ({len(files)} Markdown files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
