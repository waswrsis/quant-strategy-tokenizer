# Pre-Deployment Check Agent Prompt

```text
Before deploying or restarting a live strategy, verify:

1. Which instance is targeted:
   - public or private
   - local or remote
   - strategy_id / instance_id / cid_prefix

2. Parameters:
   - current live command
   - script defaults
   - code defaults
   - state-persisted parameters
   - public/private differences

3. Process handling:
   - identify existing process
   - stop only the intended process
   - confirm it is stopped
   - start the intended version
   - confirm command-line arguments are correct

4. State and logs:
   - do not delete state unless explicitly instructed
   - clean only logs that can contaminate diagnosis
   - preserve backups before destructive actions

5. Post-start monitoring:
   - confirm no immediate exceptions
   - confirm market data works
   - confirm order/state/audit loops work
   - confirm no unintended flatten/freeze/circuit-breaker state
```

