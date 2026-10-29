# Observed-event contract and current coverage

No live Codex-to-physical-Atom acceptance has been performed.

| Input | Current behavior | Evidence |
| --- | --- | --- |
| UserPromptSubmit | Working, retires previous turn | Automated reducer/ingress tests |
| PreToolUse | Working; preserves pending request and unacknowledged error | Automated tests |
| PermissionRequest | Needs input; observer emits no decision | Automated hook/ingress tests |
| PostToolUse | Clears only matching request; fallback identity only when no source ID exists | Automated reducer tests |
| Stop | Finished/stopping-turn cue, never inferred success | Automated mapping test; exact app lifecycle still requires live qualification |
| Interrupt | Interrupted; no happy completion | Automated reducer test |
| SessionEnd | Removes session | Implemented, live event delivery not qualified |
| SubagentStop | Ignored; cannot complete parent | Automated hook test |
| General clarification question | No automatic detector | Unsupported by the confirmed hook mappings |
| Peer/agent incoming message | Manual event supported | Automatic event route unverified |
| Approval dismissed without execution | May retain waiting state | No confirmed resolution event; no fabricated detection |
| Explicit task failure | Manual error event supported | Automatic failure mapping not confirmed |

Only status identifiers and opaque hashes are forwarded. Duplicate HTTP deliveries with the same event ID are suppressed. A provided source event ID is hashed and retained; otherwise an invocation ID distinguishes separate Stops after continued work. Repeating an already-finished state without intervening activity does not re-arm an acknowledged cue. Hook-invocation monotonic timestamps reject reversed delivery; process scheduling before hook execution is outside that guarantee.
