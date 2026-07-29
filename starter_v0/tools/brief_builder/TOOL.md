---
name: brief_builder
track: core
kind: local_formatter
requires_env: []
inputs: [items, audience, objective, max_items]
outputs: [brief, item_count, included_count]
side_effect: false
---
# brief_builder

Builds a concise demo or report brief from already-collected research items.

Use this only after lookup, social_search, timeline, fetch, papers, policy, or
other collection tools have returned items. It does not search or read URLs.
