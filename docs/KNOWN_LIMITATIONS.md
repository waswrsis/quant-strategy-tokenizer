# Known Limitations

- No broad runtime execution for current strategy graphs.
- No production broker, exchange, portfolio, or order-management integration.
- No optimizer or risk engine.
- No sandbox for custom token Python entrypoints.
- Panel reference numeric behavior is semantic float64 and is not bit-exact
  across every possible hardware/library environment.
- Installed distribution integrity is tied to the local environment and does
  not prove reproducible builds.
- Historical construction and acceptance documents are archived and
  non-normative.
