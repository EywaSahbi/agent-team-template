# tools/ — team tooling

> Back to the [project README](../README.md). Owned by lead; changes here are human decisions.

| Path | What it does |
|---|---|
| [board.py](board.py) | the team's message board: the agents and humans talk through one pinned GitHub issue (`init`, `post`, `inbox`, `wait`, `log`, `whoami`) |
| [team.conf](team.conf) | roles, logins, the paths each role may commit, the board issue number; read by `board.py` and the hook |
| [hooks/pre-commit](hooks/pre-commit) | folder-ownership guard: each role may only commit inside its own paths |
| [test_board.py](test_board.py) | checks for the board's routing and the hook: `python3 -m unittest discover tools` |

Enable once per clone:

```bash
git config core.hooksPath tools/hooks
git config team.role <role>          # a role from team.conf
```

The rules are in [AGENTS.md](../AGENTS.md).
