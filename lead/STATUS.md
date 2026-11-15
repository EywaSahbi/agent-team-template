# lead/ status (run by `<login>`, manager agent)

Keep this current: a fresh lead session resumes from it.

## Backlog (top = next)

- [ ] `AGENTS.md`: product, architecture principle, team table, diagram, hard rule 2, stack, DECISION list
- [ ] `tools/team.conf`: roles, logins, paths (same as the table in `AGENTS.md`)
- [ ] Board: `python3 tools/board.py init` (creates and pins the issue, writes its number to `tools/team.conf`)
- [ ] One folder per role from `templates/role/` (`templates/qa/` for a verifier); first backlog in each `STATUS.md`
- [ ] `docs/plan.md`: milestones with times, handoffs, demo story, budget
- [ ] Humans: schedule (start, deadline, demo format), judging / acceptance criteria → `docs/plan.md`
- [ ] M0: collect `CONTRACT.md` v1 from every publishing role; check they fit together
- [ ] M0: check each stub / skeleton as its `DONE` lands
- [ ] M1: end-to-end walk of the demo story; `docs/demo-script.md`
- [ ] M2: `README.md` for the submission / release

## Published

- `AGENTS.md`, `tools/board.py`, `tools/hooks/pre-commit`, `tools/team.conf`, `docs/plan.md`

## Decisions

One line each: `- <decision> (<who>, <date>).`
