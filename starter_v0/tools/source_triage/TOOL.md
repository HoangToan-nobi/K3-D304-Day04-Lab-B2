---
name: source_triage
track: core
kind: local_formatter
requires_env: []
inputs: [items, query, max_items]
outputs: [items, input_count, output_count, warnings]
side_effect: false
---
# source_triage

Scores already-collected research items for presentation priority.

Use this only after lookup, social_search, timeline, fetch, policy, or papers
has returned items. It does not search the web, read URLs, or verify facts.
