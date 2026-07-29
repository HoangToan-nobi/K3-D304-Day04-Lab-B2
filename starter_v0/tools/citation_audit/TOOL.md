---
name: citation_audit
track: core
kind: local_formatter
requires_env: []
inputs: [items]
outputs: [item_count, citation_ready_count, issues, passed]
side_effect: false
---
# citation_audit

Checks whether already-collected research items are ready to cite in a report or
digest.

Use this only after another tool has returned items. It does not search, fetch,
or verify facts.
