# Adapter Authoring Contract

The cleanline baseline does not ship production adapters. Future adapters must
be external integration layers that consume QST artifacts and return structured
results without changing core strategy semantics.

Adapter authors must:

- keep adapter identity and version explicit,
- preserve input and output artifact hashes,
- avoid changing strategy canonical bytes,
- report diagnostics rather than mutating strategy payloads,
- keep external credentials and broker state outside QST documents.
