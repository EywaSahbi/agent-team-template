# <role>/ — <what this role builds, in a few words> (run by `<login>`, <Claude Code | Codex | Kiro | ...>)

You build <one sentence>. You write only in `<role>/` (exact paths: `tools/team.conf`). You may read and run everything else.
This brief is a starting point from lead; refine it. Changes that affect other roles go out as a `CONTRACT` message.

## What you build

1. **M0:** `CONTRACT.md` v1 (what you publish for others) and a stub that answers in that shape, so your consumers can build against it now.
2. **M1:** <the part of the minimum result that is yours, end to end>.
3. **M2:** <what makes it expert-grade>.

<Rules that are specific to this role, e.g. which hard rule it is most likely to break and how to stay clear of it.>

## Publishes

`<role>/CONTRACT.md` and <endpoints on :<port> / files under `<role>/<path>` / a package>.

## Depends on

- **<other role>:** <what, by which milestone>. Until it lands: <the mock you use, matching their contract>.

## Commands

lead runs these after every `DONE`; keep them working.

```bash
cd <role> && <install>      # once
cd <role> && <test>         # the checks
cd <role> && <run>          # serves on :<port>
```
