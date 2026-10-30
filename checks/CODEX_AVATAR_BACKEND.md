# Codex desktop pet backend check

Inspected the installed Codex desktop 26.1023.6123.0 resources and the actual desktop Codex backend, version 0.165.0-alpha.1.2. This was read-only; the app was not patched.

The avatar overlay derives its poses from application notifications: loading maps to running, warning to waiting/Needs input, danger to failed/Blocked, success to review/Ready, and info to informational notifications. Its implementation is a renderer-side notification/activity store, rather than a separate robot-control backend.

The generated desktop protocol exposes thread/list, thread/read, thread read-state updates and hooks/list; no pet/mascot activity subscription was present. The default local app-server control socket was not available for attaching another client to the running desktop worker. A separately started app server does not subscribe to that worker's loaded threads.

The hardware companion therefore reuses the supported native UserPromptSubmit, PreToolUse, PermissionRequest, PostToolUse and Stop hook interface. Its read-only local lifecycle adapter fills structured question/answer events and immediate delivery for running chats. The adapter never reads desktop pixels or derives waiting states from prose. Only status identifiers and hashes are sent over USB. Routine new-message and child-agent alerts are disabled to keep Working uninterrupted.

This is not a claim that private Electron IPC can never be extended. It records the available supported integration surface on the installed version. If a public avatar/activity stream is exposed later, it can replace the local record adapter while retaining the same reducer and USB transport.
