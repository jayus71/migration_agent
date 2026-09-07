# Writing Style Extractor

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that extracts writing style DNA from any written content.

## What It Does

Feed it any text — a tweet, newsletter, blog post, sales page, book chapter, email — and it produces:

- **`{source}-style-profile.json`** — Structured style profile covering 8 dimensions
- **`{source}-style-report.md`** — Human-readable analysis with quoted examples

## Analysis Layers

The skill deconstructs writing through **6-layer cognitive archaeology**:

1. **Surface Patterns** — Formatting, punctuation, vocabulary, structure
2. **Psychological Architecture** — Persuasion frameworks, emotional triggers
3. **Subconscious Rhythms** — Pacing, flow, musical qualities
4. **Linguistic Fingerprints** — Unique syntax and structural preferences
5. **Influence Mechanisms** — How style creates psychological impact
6. **Replication Blueprint** — Actionable framework for recreating the style

## Installation

Add to your Claude Code project:

```bash
claude install-skill shannhk/writing-style-extractor
```

## Usage

Just ask Claude to analyze any writing:

- *"Analyze the writing style of this blog post"*
- *"Extract the style DNA from these tweets"*
- *"Break down how this author writes"*

Accepts pasted text, URLs, or local file paths.

## Credits

Based on the style extraction framework by **Machina** ([@exm7777](https://x.com/exm7777)) on X.

## License

MIT
