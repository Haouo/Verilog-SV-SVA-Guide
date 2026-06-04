# Authoring Conventions

This guide is a mirrored bilingual set of Markdown files. These conventions keep
it consistent and easy to maintain.

## Writing style

- **Plain, academic English.** Avoid rare or fancy words. Prefer short,
  declarative sentences. Be concise and direct.
- The Traditional Chinese edition follows the same restraint: clear and compact,
  no filler.
- Keep technical terms in English in both editions. Give the Chinese gloss on
  first use, drawn from [GLOSSARY.md](GLOSSARY.md).

## Chapter template

Every chapter follows the same shape:

1. **Title + nav line** — links to previous/next chapter and back to the TOC.
2. **Learning objectives** — a short bulleted list.
3. **Concept explanation** — the body, broken into sections.
4. **Illustrative snippets** — short, focused code. Not a runnable project.
5. **Design-intent callout** — a blockquote that ties the topic back to what a
   designer is trying to express. Marked `> **Design intent.**`.
6. **Common pitfalls** — a list of mistakes and how to avoid them.
7. **Summary** — a few bullets.
8. **Footer nav** — previous/next links.

## Code blocks

- Fence Verilog with ` ```verilog ` and SystemVerilog with ` ```systemverilog `.
- Fence non-code alignment tables or mapping summaries with ` ```text `.
- Comments inside code stay in English in both editions.
- Keep snippets minimal: show the point, omit boilerplate unless it matters.

## Files and structure

- The same filenames exist under `en/` and `zh-TW/`, with matching heading
  structure, so the two editions stay in lockstep.
- Keep each file focused and under ~800 lines. Split a topic before it grows
  past that.
- Use **relative Markdown links** only. No external build tooling.
- Track editorial state in [docs/CONTENT_STATUS.md](docs/CONTENT_STATUS.md).

## Local checks

Run the repository-local documentation checker before committing:

```text
python3 tools/check_docs.py
```

It checks mirrored bilingual files, relative Markdown links, code fence labels,
heading shape, and required design-intent callouts.

## Cross-references

- Link to other chapters with relative paths.
- When you introduce a glossary term for the first time in a chapter, link it to
  [GLOSSARY.md](GLOSSARY.md) or restate the gloss inline.

## Reference standards

Author against the governing source, cited per part in
`appendices/D-references.md`:

- Part I — IEEE 1364-2005 (Verilog).
- Part II — IEEE 1800-2023 (SystemVerilog).
- Part III — IEEE 1800-2023 assertion clauses, plus the SVA literature.
