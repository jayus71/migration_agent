---
name: writing-style-extractor
description: >
  Extract and analyze writing style DNA from any written content, producing a detailed
  style profile as both a structured JSON file and a human-readable markdown report.
  Use when the user asks to: analyze writing style, extract voice or tone, deconstruct
  how someone writes, create a style profile, study an author's patterns, reverse-engineer
  writing style, capture a brand voice, or perform stylometric analysis.
  Triggers on: "analyze this writing", "extract the style", "how does this person write",
  "style profile", "voice analysis", "writing DNA", "deconstruct this content",
  "analyze the tone", "what makes this writing work", "break down this style".
  Accepts input as: pasted text, URLs, or local file paths.
  Supports all content types: tweets, newsletters, blog posts, book chapters, sales pages,
  emails, landing pages, ad copy, speeches, academic writing, technical docs, etc.
---

# Writing Style Extractor

Deconstruct any written communication to its molecular level, revealing the hidden
psychological architecture that creates influence, engagement, and memorability.

Expertise applied: advanced stylometric analysis, copywriting psychology, linguistic
fingerprinting, subconscious pattern detection, psychological trigger identification.

## Workflow

### 1. Gather Content

Handle all input types:
- **Pasted text**: Analyze directly
- **URLs**: Fetch page content, then analyze
- **Local files**: Read file contents, then analyze
- **Multiple samples**: When provided, cross-validate patterns across samples for higher confidence

### 2. Context Discovery

Before analysis, identify:
- Content type (tweet, newsletter, book chapter, sales page, email, etc.)
- Author/source if known
- Intended audience (if discernible)
- Platform conventions that may influence style

### 3. Six-Layer Cognitive Archaeology

Extract style systematically through these layers:

| Layer | Focus | What to capture |
|-------|-------|-----------------|
| **Surface Patterns** | Formatting, punctuation, vocabulary, structure | Sentence length distribution, paragraph patterns, signature words, punctuation habits |
| **Psychological Architecture** | Persuasion frameworks, emotional triggers | AIDA/PAS usage, emotional arcs, scarcity/authority/social proof signals |
| **Subconscious Rhythms** | Pacing, flow, musical qualities | Short-long alternation, tension-release cycles, alliteration, cadence |
| **Linguistic Fingerprints** | Unique syntax and structural preferences | Sentence openers, transition patterns, fragment usage, voice (active/passive) |
| **Influence Mechanisms** | How style creates psychological impact | Hook patterns, curiosity loops, open loops, callback techniques |
| **Replication Blueprint** | Actionable framework for recreating style | Non-negotiable elements, dos/donts, consistency rules |

**Precision standard**: Analysis must be precise enough that someone could write content
virtually indistinguishable from the original author.

### 4. Quality Gates

Every identified pattern must be:
- **PRECISE**: Backed by specific quoted examples from the content
- **COMPREHENSIVE**: No significant stylistic element overlooked
- **ACTIONABLE**: Translatable into concrete writing guidance
- **DEEP**: Surface observation paired with psychological mechanism
- **CONSISTENT**: Validated across multiple instances in the sample
- **UNIQUE**: Captures what distinguishes this style from generic writing

Assign a confidence score (0.0-1.0) to each major finding based on evidence strength.

### 5. Output Generation

Generate **two files** in the current working directory:

#### `{source}-style-profile.json`

Structured JSON profile. See [references/json-schema.md](references/json-schema.md) for the
complete schema with all fields and descriptions.

#### `{source}-style-report.md`

Human-readable markdown report structured as:

```
# Style Analysis: {Author/Source}
## Overview (content type, sample size, uniqueness score, top 3 signature traits)
## Surface Patterns (with examples)
## Psychological Architecture (with examples)
## Subconscious Rhythms (with examples)
## Linguistic Fingerprints (with examples)
## Influence Mechanisms (with examples)
## Replication Blueprint (actionable rules)
## Effectiveness Assessment (strongest techniques, uniqueness factors)
```

Every section must include direct examples from the source material.

**File naming**: Use kebab-case author name or source descriptor.
Examples: `seth-godin-style-profile.json`, `company-newsletter-style-report.md`
