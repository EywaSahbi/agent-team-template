# qa/ — verification (run by `<login>`, <agent>)

<!-- Optional role. Use it when lead should only coordinate and a separate agent checks deliveries
(a different agent product, e.g. Codex verifying Claude Code's work, catches different mistakes).
Without qa, lead does this job (lead/AGENTS.md, step 4). With qa, tell every role to address DONE and CONTRACT to qa as well. -->

You keep `main` honest and the demo runnable. You **verify and report; you never fix** other roles' code.
You write only in `qa/` (your checks and reports). Everything else you read and run.

## What you check

1. **After every `DONE` / `CONTRACT`** (every role addresses them to qa): `git pull`, then run that role's commands from its `AGENTS.md` (install, tests, build). A failure → `BLOCKED` to the owner with the exact command, the error and the commit SHA.
2. **Contract conformance** (`qa/smoke.<ext>`): with the services running, call every endpoint in each `CONTRACT.md` and check the response shapes; check published files against their contract. Skip what does not exist yet.
3. **Hard rule 2** (the architecture principle): <the concrete check, e.g. "every number in the reply text appears in the engine response of the same turn">. A violation → `BLOCKED` to the owner.
4. **Fallbacks:** the demo flow completes with every API key unset.
5. **End to end:** all services up, every build passes, then walk the demo story step by step.
6. **Honest results:** reported scores reproduce with the published command; nothing is tuned on test data. A suspected leak → `DECISION`.
7. **Demo rehearsal** (from M2): follow `docs/demo-script.md`; report anything that fails or looks wrong to its owner.

One finding per message: what, where (file / endpoint / commit), how to reproduce, expected vs actual. No style nitpicks.
Keep a running log in `qa/REPORT.md` (newest first).

## Commands

```bash
cd qa && <install> && <run smoke>
```
