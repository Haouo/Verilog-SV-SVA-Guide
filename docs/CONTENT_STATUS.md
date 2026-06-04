# Content Status

[← Back to top](../README.md)

This file records the editorial state of the guide. It is intentionally separate
from the table of contents: the table of contents tells readers where to go, and
this file tells contributors what still needs review.

## Status legend

| Status | Meaning |
|---|---|
| Drafted | The chapter has a complete first pass and can be read end to end. |
| Mirrored | The English and Traditional Chinese files exist with matching structure. |
| Source-check pending | The text should still be checked against the cited standards and references. |
| Reviewed | A knowledgeable reviewer has checked the technical claims and examples. |

## Current matrix

All current chapters are drafted, mirrored, and have received a first
narrative-deepening pass. The next editorial pass should focus on source-checking
and reviewer notes.

| Section | Files | Editorial state | Next useful pass |
|---|---:|---|---|
| Orientation | 2 | Drafted, mirrored, deepened | Source-check framing and audience claims |
| Part I - Verilog for Design | 16 | Drafted, mirrored, deepened | Check examples against IEEE 1364-2005 |
| Part II - SystemVerilog for Design | 14 | Drafted, mirrored, deepened | Check design-subset guidance against IEEE 1800-2023 |
| Part III - SystemVerilog Assertions | 32 | Drafted, mirrored, deepened | Check SVA semantics, examples, and edge cases |
| Appendices | 8 | Drafted, mirrored, deepened | Check reference completeness and quick-reference accuracy |
| Shared glossary | 1 | Drafted | Expand when new translated terms appear |

## Chapter checklist

Use this checklist when editing or reviewing a chapter:

- The English and Traditional Chinese files both exist.
- The heading structure matches between languages.
- The chapter has learning objectives, examples, a design-intent callout, common
  pitfalls, a summary, and footer navigation.
- Code fences use `verilog`, `systemverilog`, or `text`.
- New translated terms are added to `GLOSSARY.md` before they spread across
  chapters.
- Relative links pass `python3 tools/check_docs.py`.

## Automation

Run the local documentation checker before committing:

```text
python3 tools/check_docs.py
```

The checker validates mirrored files, Markdown links, code fence labels, heading
shape, and required design-intent callouts.
