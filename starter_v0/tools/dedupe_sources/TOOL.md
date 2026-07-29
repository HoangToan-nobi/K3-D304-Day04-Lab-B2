---
name: dedupe_sources
track: core
kind: local_formatter
requires_env: []
inputs: [items, max_items]
outputs: [items, input_count, output_count, removed_count]
side_effect: false
---
# dedupe_sources

Removes duplicate research items before formatting a digest.

Use this only after another tool has already returned items. It does not search,
fetch, or verify new information.
