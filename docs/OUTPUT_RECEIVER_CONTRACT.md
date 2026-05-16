# Output Receiver Contract

Output receivers consume QST artifacts after validation. They do not define
strategy semantics.

Receivers should:

- accept only canonical JSON-compatible payloads,
- check artifact ids and parent hashes,
- treat diagnostics as structured data,
- keep wall-clock or environment observations out of semantic hashes,
- avoid writing back into source strategy documents.
