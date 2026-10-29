# Automatic Codex event coverage

2026-10-30: A background companion was connected to the physical AtomS3R + Echo Base on Windows. Real local Codex start/activity/message/completion records were observed. A genuine scope-selection question produced Needs input and its user's answer produced Resolved. The device handshake and serial connection were live. Physical expression quality and audibility still depend on the user's inspection.

| Source | Behavior | Validation |
| --- | --- | --- |
| task_started | Working | Live Codex record |
| completed command/tool/file item | Working underneath temporary messages | Live records and tests |
| assistant commentary item | New message for 3 seconds | Live record and tests |
| request_user_input / request_user_input_async | Needs input keyed by call ID | Live asynchronous question and tests |
| synchronous tool answer / structured asynchronous answer | Clears only the matching wait | Live answer and tests |
| task_complete | Finished; outstanding input and other active work retain priority | Live completion records and tests |
| child-agent interaction/completion item | New message; never finishes the parent | Structured-item tests |
| turn_aborted | Paused | Parser support; live interruption not qualified |
| UserPromptSubmit / PreToolUse / Stop hooks | Native start/activity/completion route | Installed and exact definitions trusted |
| PermissionRequest hook | Needs input; no approval decision | Installed and native API confirms trusted |
| PostToolUse hook | Resolves only matching request | Installed/trusted and ingress tests |
| dismissed approval with no execution/result event | May retain waiting state | Not live-qualified |
| ordinary prose question without a structured input tool | No question inference | Intentional: no prompt-text heuristics |

The local JSONL format is not a stable public API. Unknown records are ignored. This adapter is checked against the installed desktop Codex 0.165.0-alpha.1.2 format (the CLI 0.149.1 hook protocol was also inspected); format changes may require updating it. New events are observed without replaying historical alerts. Other Codex homes and cloud-only chats need separate event sources. No prompt, answer, source-code or reasoning text is forwarded to the robot.
