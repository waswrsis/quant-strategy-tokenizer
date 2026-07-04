# v0.4 Compatibility Boundary

## Preserved Contracts

Until Stage 7 migration acceptance proves otherwise, the following are frozen v0.4
compatibility contracts:

- `qst-ir/0.4` and `qst-canonical/0.4` document identities;
- `.gkr.yaml` editable strategy sources;
- graph, parameter, and instance hash behavior;
- accepted built-in TokenSpec and TokenPack behavior;
- vocabulary, validate, hash, and canonicalize CLI behavior;
- the 12 public strategy demos and their reference hashes;
- Qlib workflow import as a partial record-layer proof.

## Legacy-Only Capability

The v0.4 custom runtime can import and execute approved custom Python. QST 1.0 does not
adopt that behavior as a core capability. It will be isolated behind `qst.compat.v04`
or removed from the 1.0 CLI only after migration tests and documentation are available.
Until then, its presence is legacy behavior, not a new-architecture guarantee.

## Compatibility Test Rule

Every stage runs the existing v0.4 test suite. A deliberate compatibility change
requires an explicit supersession record and cannot be hidden inside an unrelated
stage.

