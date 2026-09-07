# Style Profile JSON Schema

## Top-Level Structure

```json
{
  "style_metadata": {},
  "surface_characteristics": {},
  "psychological_architecture": {},
  "rhythm_and_flow": {},
  "influence_mechanisms": {},
  "voice_personality": {},
  "replication_blueprint": {},
  "effectiveness_assessment": {}
}
```

## Field Definitions

### style_metadata

| Field | Type | Description |
|-------|------|-------------|
| `content_type` | string | Type of content analyzed (tweet, newsletter, blog, etc.) |
| `source` | string | Author name or source attribution |
| `sample_size` | object | `{ "word_count": int, "piece_count": int }` |
| `analysis_date` | string | ISO 8601 date |
| `confidence_level` | float | Overall analysis confidence (0.0-1.0) |
| `uniqueness_score` | float | How distinctive the style is vs generic writing (0.0-1.0) |

### surface_characteristics

| Field | Type | Description |
|-------|------|-------------|
| `formatting` | object | Paragraph length tendencies, header usage, list patterns, bold/italic habits |
| `vocabulary` | object | Reading level, jargon density, signature words/phrases (array), word frequency patterns |
| `structure` | object | Sentence length distribution (min/max/avg/mode), paragraph patterns, opening/closing formulas |
| `punctuation` | object | Em dash frequency, ellipsis patterns, exclamation use, semicolon preference, comma style |
| `capitalization` | object | Title case vs sentence case, emphasis capitalization, ALL CAPS patterns |
| `examples` | array | Quoted examples demonstrating each pattern |

### psychological_architecture

| Field | Type | Description |
|-------|------|-------------|
| `persuasion_frameworks` | array | Primary models used (AIDA, PAS, BAB, 4Ps, etc.) with confidence |
| `emotional_appeals` | object | Dominant emotions targeted, emotional arc pattern, intensity range |
| `triggers` | array | Psychological triggers employed (scarcity, authority, social proof, reciprocity, etc.) |
| `positioning` | object | Author's stance relative to reader (peer, mentor, authority, challenger, insider) |
| `examples` | array | Quoted examples demonstrating each pattern |

### rhythm_and_flow

| Field | Type | Description |
|-------|------|-------------|
| `pacing_patterns` | object | Fast/slow alternation, buildup patterns, tension-release cycles |
| `musical_qualities` | object | Alliteration frequency, assonance, consonance, rhythmic signatures |
| `cognitive_load` | object | Information density management, complexity variation, breathing room patterns |
| `sentence_cadence` | object | Short-long patterns, fragment usage, run-on tendencies, list rhythms |
| `examples` | array | Quoted examples demonstrating each pattern |

### influence_mechanisms

| Field | Type | Description |
|-------|------|-------------|
| `attention_capture` | object | Hook patterns, opening strategies, pattern interrupts |
| `engagement_maintenance` | object | Curiosity loops, open loops, callbacks, nested storytelling |
| `behavioral_influence` | object | CTA patterns, decision architecture, nudge techniques |
| `examples` | array | Quoted examples demonstrating each pattern |

### voice_personality

| Field | Type | Description |
|-------|------|-------------|
| `character_traits` | array | Dominant personality traits expressed (e.g., "contrarian", "empathetic", "irreverent") |
| `communication_style` | object | Formal/informal spectrum (1-10), directness level (1-10), humor type and frequency |
| `value_expression` | array | Core values communicated, belief signals, identity markers |
| `relationship_to_reader` | object | Primary stance, power dynamic, intimacy level |
| `examples` | array | Quoted examples demonstrating each pattern |

### replication_blueprint

| Field | Type | Description |
|-------|------|-------------|
| `essential_elements` | array | Non-negotiable style elements for accurate replication |
| `practical_guidelines` | array | Concrete writing rules to follow (e.g., "Start 40% of sentences with 'And' or 'But'") |
| `consistency_rules` | array | What must remain constant across all content |
| `dos` | array | Specific patterns to always use, with examples |
| `donts` | array | Specific patterns to always avoid, with examples |

### effectiveness_assessment

| Field | Type | Description |
|-------|------|-------------|
| `strongest_techniques` | array | Most impactful style elements, each with example and impact description |
| `sophistication_level` | float | Technical writing craft sophistication (0.0-1.0) |
| `uniqueness_factors` | array | What specifically makes this style distinct from others |
| `confidence_scores` | object | Per-category confidence ratings (0.0-1.0) keyed by category name |
