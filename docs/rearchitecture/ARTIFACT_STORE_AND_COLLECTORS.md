# Artifact Store and Collectors

QST stores opaque artifact bytes by raw SHA-256 digest using bounded 4 MiB reads. Writes
are staged in the store directory and atomically moved into a digest path. Existing
objects are deduplicated and never overwritten.

Chunk size must be positive. A deduplication hit is rehashed before acceptance, so
same-size corruption cannot be hidden by the digest path. Descriptor, activity, and
artifact identities are revalidated at store/index/collector trust boundaries.

Sealed descriptor JSON is authoritative metadata. The SQLite WAL database is a local,
derived index that can be deleted and rebuilt from descriptor files. It is not a remote
coordination backend.

Collectors implement observation only. The `EvidenceAdapter` protocol contains
`probe`, `discover`, `extract_plan`, `collect_run`, `describe_artifacts`, and `verify`;
it intentionally contains no `execute` method.

Activity snapshots follow the frozen transition graph documented by the evidence
kernel. Verified result evidence requires a sealed verified activity and an exact match
between its output artifact IDs and sealed descriptors.
Verified activities and verified result payloads cannot have an empty artifact set.

Performance targets remain measurement targets, not unsupported claims: bounded stream
reads, default responses under 4 KiB in future CLI/API layers, and local index rebuilds
without re-hashing unchanged object bytes.
