# Entity Registry Schema (no-proper-nouns gate)

ADOPT of the shuohao-skills no-names doctrine
(docs/extraction/shuohao-skills/no-names-doctrine.md, WD-4k56/qbcj).
Source: github.com/eternityspring/shuohao-skills, Apache-2.0.

## Purpose

Image/video generation prompts must never contain proper nouns the
model might "know" — named characters, aliases, real people, places,
IP. Models bias toward their memorized version of a named entity and
will draw *their* character, not yours. The gate
(`gates/no_names_gate.py`) enforces this deterministically against
this registry: exact, case-insensitive, word-boundary-anchored
matching of registry names and aliases. No LLM, no network.

## What is an entity (and what is NOT)

ENTITIES (register these):
- Named characters from SGFLIX character bibles (name + all aliases)
- Named invented places/worlds from bibles
- IP names and work titles
- Real people / public figures (likeness leakage — strongest case)

NOT entities (do NOT register):
- Common nouns used generically in our banked intents: lighthouse,
  kaiju, heron, snowplow, koi — these are legitimate prompt vocabulary
- Film-stock / hardware / era vocabulary the briefs deliberately use:
  Kodak Vision3 500T, IBM 3420-type, PS2, S-VHS — these carry the
  aesthetic; they are prompt payload, not identity

Rule of thumb: register a name only if the model "knowing" it would
drag in the wrong identity. Registering "Kaiju" as an entity name
would then (correctly, by boundary semantics below) block the phrase
"the kaiju stirs" — so do not do it unless Kaiju is a bible
character's actual name.

## File format

JSON, one file, default location `datasets/entity-registry.json`:

```json
{
  "version": 1,
  "entities": [
    {
      "id": "char-mira-chen",          // unique, stable
      "type": "character",             // character|place|ip|person|work
      "name": "Mira Chen",             // canonical name (required)
      "aliases": ["Mira", "the Ferry Girl"],
      "source": "bible gist URL / provenance"  // optional
    }
  ]
}
```

`load_registry()` validates: object with `entities` array; each entity
has a nonempty string `name`; `type` in the enum; aliases are
nonempty strings. Invalid registries raise ValueError loudly.

## Matching semantics (explicit)

- EXACT match only: surface forms must equal a `name` or `alias`.
  No stemming, no fuzzy match, no LLM.
- Case-insensitive: "mira", "Mira", "MIRA" all hit.
- Word-boundary anchored: a match must not touch a word character
  (`[A-Za-z0-9_]`) on either side.
  - "Kaiju" registered → hits "Kaiju rising", "the Kaiju stirs",
    "kaiju," — does NOT hit "kaijur", "kaijux", "Miramar",
    "admiral", "godzillaverse".
  - Multiword names match the exact phrase; internal single spaces in
    the registry entry match any whitespace run in the text
    ("Vermilion  Bay" hits "Vermilion Bay").
- Longest surface wins: if "Mira Chen" (alias) and "Mira" (shorter)
  overlap, the longer alias is reported once, not both.

## Wiring

- Brief validation: `predict/prompt_director.RenderBrief(registry=...)`
  rejects any section containing a registry name with a typed
  ValueError, same pattern as the meta-hint guard. `registry=None`
  (default) SKIPS the gate with a loud warning — never silently
  (doctrine: missing cast list skips loudly).
- Standalone CLI: `scripts/check_names.py <file-or-text>
  [--registry PATH]` — exit 0 clean, 1 violations, 2 registry error.

## Decision provenance vs fact provenance (separate trails, WD-oyti)

ADOPT of the shuohao-skills from/mergeNote ↔ inferred split
(docs/extraction/shuohao-skills/inferred-marker-convention.md):
adaptation-level provenance records provenance of DECISIONS; the
`(inferred)` marker records provenance of FACTS. Two different audit
trails that NEVER mix.

- **Fact provenance** (this file's gate + `gates/provenance_gate.py`):
  every identity claim in an entity record or render brief carries
  either a canon citation (`source`) or exactly one `(inferred)`
  marker. No unmarked middle ground. Markers are stripped at
  handoff-to-prompt time (`host/wangp_adapter.brief_to_prompt`).
- **Decision provenance** (new optional fields on entity records):
  - `from`: who merged into whom during bible adaptation
    (e.g. `"from": ["char-lead-a", "char-lead-b"]`).
  - `mergeNote`: WHY the lead group was chosen — the decision's
    rationale, verbatim where possible.

```json
{
  "id": "char-mira-chen",
  "type": "character",
  "name": "Mira Chen",
  "aliases": ["Mira"],
  "source": "bible gist URL / provenance",   // FACT trail (canon citation)
  "from": ["char-lead-a"],                    // DECISION trail (optional)
  "mergeNote": "kept as lead: source quotes her in 4 of 6 scenes"
}
```

`load_registry()` tolerates the two optional decision fields (they are
audit metadata, not matching inputs — names/aliases only feed the
gate). A record may carry both trails simultaneously; they describe
different questions ("where does this fact come from?" vs "why did we
make this adaptation choice?") and must not be conflated.

## Maintenance

Bible ingestion should append entities (name + aliases verbatim from
the CHARACTER_IDENTITY_LOCK) — never hand-edit generated entries.
Seed registry currently contains placeholder examples pending the
first bible ingestion; replace them then.
