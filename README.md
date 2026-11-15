# Agent team template

A base for projects built by a team of coding agents (Claude Code, Codex, Kiro, ...) and their humans in one repo.
Each agent owns a part of the repo, the agents hand work to each other on a message board (one pinned GitHub issue), a **lead** agent runs the team, and the humans step in only for critical decisions.

> Starting a project from this template? Replace this README with your project's; the guide stays in [docs/GUIDE.md](docs/GUIDE.md).

## What is inside

| Path | What |
|---|---|
| [AGENTS.md](AGENTS.md) | the operating rules every agent reads first: product (placeholders), ownership, message board, agent loop, when to ask a human, hard rules, working style, setup |
| [CLAUDE.md](CLAUDE.md) | loads `AGENTS.md` for Claude Code, plus how Claude Code waits on the board |
| [tools/board.py](tools/board.py) | the message board CLI: `init`, `post`, `inbox`, `wait`, `log`, `whoami` (Python stdlib + `gh`) |
| [tools/team.conf](tools/team.conf) | roles, the GitHub login running each, the paths each may commit, the board issue |
| [tools/hooks/pre-commit](tools/hooks/pre-commit) | ownership guard: each role commits only inside its own paths |
| [lead/](lead/) | the manager agent's brief and status |
| [templates/role/](templates/role/) | brief, status and contract skeletons for a new role folder |
| [templates/qa/](templates/qa/) | an optional verifier role that checks every delivery and never fixes |
| [docs/plan.md](docs/plan.md) | milestones M0–M3, handoffs, demo story, budget, decisions |
| [docs/GUIDE.md](docs/GUIDE.md) | how to set up a project, cut roles, write the architecture principle, and why it works this way |
| [.codex/config.toml](.codex/config.toml), [.claude/settings.json](.claude/settings.json) | agent configs: network for Codex's sandbox, pre-approved board commands for Claude Code |

## Quick start

```bash
gh repo create <owner>/<project> --private --template EywaSahbi/agent-team-template --clone
cd <project>
# 1. fill in AGENTS.md (product, architecture principle, team table) and tools/team.conf (roles, logins, paths)
git config core.hooksPath tools/hooks && git config team.role lead
python3 tools/board.py init                        # creates + pins the board issue, writes its number to team.conf
cp -r templates/role backend                       # one folder per role; fill in its AGENTS.md and STATUS.md
git add -A && ALLOW_SHARED=1 git commit -m "lead: project setup" && git push
```

Then every teammate clones once per role they run, follows `AGENTS.md` → Setup, and pastes the starting prompt into their agent. Full walkthrough: [docs/GUIDE.md](docs/GUIDE.md).

## How the agents talk

```bash
python3 tools/board.py post --to backend --type NEED "Need POST /sessions returning {id} by M0; mocking it meanwhile"
python3 tools/board.py inbox                       # unread messages for this clone's role
python3 tools/board.py wait                        # block until one arrives (Claude Code: as a background command)
```

Message types: `NEED` · `DONE` · `CONTRACT` · `BLOCKED` · `ACK` · `FYI` · `DECISION`. The board never @-mentions anyone, so it sends no emails; humans answer in the issue with `[role]`.

Checks for the board and the hook: `python3 -m unittest discover tools`.
