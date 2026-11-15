# Plan

Humans and lead own this file; other agents propose changes with a `NEED` to lead.
Each milestone ends with a `DONE` on the board from every role that delivered into it (addressed to its consumers and lead).

<!-- lead: fill in times as soon as the humans know the schedule. Keep this file short: it is read at every session start. -->

## Milestones

| | When | <role> (<human>) | <role> (<human>) | <role> (<human>) |
|---|---|---|---|---|
| **M0 Contracts + skeletons** | <time> | `CONTRACT.md` v1; stub that answers in its shape | skeleton runs against the other roles' stubs | `CONTRACT.md` v1; first sample of its output |
| **M1 Minimum, end to end** | <time> | <real thing, demo case> | <real loop against the real services> | <...> |
| **M2 Expert-grade** | <time> | <...> | <...> | <...> |
| **M3 Freeze** | <time> | bug fixes only | bug fixes only | bug fixes only |
| **Submit / release** | <time> | | | humans submit |

lead checks every delivery as it lands, walks the full demo from M1, and owns the demo script.

**M1 is the minimum result:** <one sentence: the shortest flow that shows the product working end to end>. Nobody starts M2 work while an M1 item of theirs is open.

## Handoffs (who waits on whom)

- <role> → <role>: <what> (M0), <what> (M1).
- <role> ↔ <role>: <the shared list or format both contracts must agree on> (M0).

## Demo story

<Three to five numbered steps a judge / user sees, in order. Lines to say: `docs/demo-script.md`.>

## Budget

<Which paid APIs and services the team already uses, on whose key. Anything else that costs money is a `DECISION`.>

## Open questions (lead asks the humans or outside experts)

- Schedule: start, deadline, format of the demo and pitch.
- Judging / acceptance criteria.

## Decided

One line each, newest last: `- <decision> (<who>, <date>).`
