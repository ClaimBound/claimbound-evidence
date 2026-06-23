# HEADROOM_SEMANTIC_FIDELITY_D004 prereg charter

## Protocol boundary

This protocol is a semantic-fidelity follow-up to D001. D001 used an exact-answer
gate. D004 uses deterministic structured-field checks so that wording drift is
allowed, but factual meaning changes are not.

## Fixed version and environment

- Headroom package: `headroom-ai==0.27.0`
- Headroom tag: `v0.27.0`
- Tag commit: `95b2333ee5a3f1cbe512ca04a6563c3572835758`
- Access date: `2026-06-23`
- Primary local model: installed Ollama `qwen2.5-coder:7b` unless overridden.
- Local hardware statement: MacBook Pro 16 inch, Apple M1 Pro, 16 GB.

## Gates

For each fixture:

1. Generate the synthetic fixture in memory.
2. Send original context to the same local Ollama model at temperature 0.
3. Compress with Headroom using the same direct local library path as D001.
4. Send compressed context to the same local Ollama model at temperature 0.
5. Parse both answers as JSON objects.
6. Compare only the predeclared semantic fields.
7. Pass only if:
   - original baseline matches expected semantic fields;
   - compressed path matches expected semantic fields;
   - token reduction is at least 60%.

## Privacy controls

- Do not commit raw prompts, raw fixture bodies or raw LLM answers.
- Commit only fixture hashes, answer hashes, token counts, semantic booleans and
  mismatched field names.
- Do not commit serial numbers, hardware UUIDs, UDIDs, credentials or private
  transcript paths.

