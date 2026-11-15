# Guide: running a team of coding agents in one repo

This repo is a base for projects where several coding agents (Claude Code, Codex, Kiro, ...) and their humans build one product together. Each agent owns a part of the repo, the agents talk to each other through one GitHub issue, and the humans step in only for decisions that are really theirs.

It was extracted from two hackathon projects that ran this way: four humans running seven agents, and three humans running six. Everything project-specific was taken out; the rules and tools that made the team work are kept.

## The pieces

| Piece | File(s) | What it does |
|---|---|---|
| **Operating rules** | [AGENTS.md](../AGENTS.md), [CLAUDE.md](../CLAUDE.md) | the one page every agent reads first: product, ownership, the board, the agent loop, when to ask a human, hard rules, working style, setup |
| **Message board** | [tools/board.py](../tools/board.py) + one pinned issue | the only channel between agents: `post`, `inbox`, `wait`, `log`. Messages are typed (`NEED`, `DONE`, `CONTRACT`, `BLOCKED`, `ACK`, `FYI`, `DECISION`) and addressed by role |
| **Team config** | [tools/team.conf](../tools/team.conf) | roles, the GitHub login running each, the paths each may commit, the board's issue number |
| **Ownership guard** | [tools/hooks/pre-commit](../tools/hooks/pre-commit) | refuses a commit that touches paths outside the clone's role |
| **Role folders** | `<role>/AGENTS.md`, `STATUS.md`, `CONTRACT.md` | the role's brief, its live backlog (what a fresh session resumes from), and the interface it publishes |
| **lead** | [lead/](../lead/) | a manager agent: plans, triages the board, checks every delivery, escalates to humans |
| **Plan** | [docs/plan.md](plan.md) | milestones M0–M3, handoffs, demo story, budget, decisions |

```
   human A           human B           human C            (chat with their own agents; answer DECISIONs)
      │                 │                 │
  ┌───┴────┐       ┌────┴───┐        ┌────┴───┐
  │ lead   │       │backend │        │frontend│           one agent per clone, one role per agent
  │ agent  │       │ agent  │        │ agent  │
  └───┬────┘       └───┬────┘        └───┬────┘
      │   post / inbox / wait (tools/board.py, via gh)
      ▼                ▼                  ▼
  ┌──────────────────────────────────────────────┐
  │   pinned issue "Agent message board"         │      hidden marker routes each comment to roles
  └──────────────────────────────────────────────┘
      │                │                  │
      ▼ git push       ▼                  ▼               pre-commit hook: each role commits only its paths
  lead/ docs/ tools/   backend/           frontend/        folders meet only through CONTRACT.md
```

## Set up a new project

1. **Create the repo** from this template ("Use this template" on GitHub, or `gh repo create <owner>/<name> --private --template <this repo>`), and clone it.
2. **Describe the product** in [AGENTS.md](../AGENTS.md): fill every `<placeholder>` and delete the `<!-- lead: -->` comments. The two parts that matter most:
   - the **architecture principle** (see below), which becomes hard rule 2;
   - the **team table**: one row per role, with what it builds.
3. **Edit [tools/team.conf](../tools/team.conf)**: one line per role, `<role> <github-login> <paths>`. Same roles as the table.
4. **Enable the hook and set your role** in your clone: `git config core.hooksPath tools/hooks && git config team.role lead`.
5. **Create the board:** `python3 tools/board.py init`. It creates the issue, pins it, and writes its number into `team.conf`.
6. **Create the role folders:** `cp -r templates/role backend` (and so on; `templates/qa` for a verifier). Fill in each brief and a first backlog: M0 is always "publish `CONTRACT.md` v1 and a stub".
7. **Fill in [docs/plan.md](plan.md)**: milestones with times, who waits on whom, the demo story.
8. **Commit the setup** as the human who set it up, and push: `git add -A && ALLOW_SHARED=1 git commit -m "lead: project setup" && git push`. `ALLOW_SHARED=1` is needed once because the new role folders are not lead's paths. From now on every role commits only its own paths.
9. **Replace [README.md](../README.md)** with your project's README.
10. **Start the agents.** Every teammate clones the repo once per role they run, then runs the setup block in `AGENTS.md` → Setup and pastes the starting prompt into their agent. Start lead first.

Check it works: in each clone, `python3 tools/board.py whoami` prints the login, role and board link without warnings. Then `python3 -m unittest discover tools` passes.

## Cutting roles

- **Cut by folder and by interface.** A role is a folder that publishes something others use: an API, files, a package. If two roles would keep editing the same files, they are one role.
- **Few roles.** Three to six worked. Every role adds a contract to keep in sync and messages to triage.
- **One agent per clone.** Each agent has its own working tree, so agents never see each other's uncommitted changes. One human may run several agents, each in its own clone with its own `team.role`.
- **Shared folders are allowed, cut by path.** `team.conf` takes path prefixes, so two roles can split one folder: `ai api/server.py api/routes/` and `ai2 api/llm api/tts.py`. Write in `AGENTS.md` who owns what and that they coordinate on the board before touching the other half.
- **Give the producers a `CONTRACT.md`.** Roles that only consume (a UI, qa) usually need none.
- **lead or qa?** lead coordinates and verifies by default. A separate `qa` role ([templates/qa/](../templates/qa/)) is worth it when lead is a human-only session, or when you want a different agent product to check the work.

## The architecture principle

Each project names one sentence that says where the truth lives, and every agent protects it. It keeps LLM-driven parts from inventing things, and it gives lead and qa something concrete to check.

- *"Numbers come from the engine, words come from the LLM."* A deterministic engine computes every size and price; the LLM layer talks, calls the engine as a tool, and explains its reasons. It never creates a number.
- *"The case is the truth, the patient only acts."* A case file holds every fact; the AI patient phrases them in character and adds none.

Write it in the product section, repeat it as hard rule 2, and give lead (or qa) a concrete check: "for a few demo turns, every number in the reply appears in the engine response of that turn".

## Milestones

| | Goal | Why |
|---|---|---|
| **M0 Contracts + skeletons** | every producer publishes `CONTRACT.md` v1 and a stub that answers in its shape | consumers build against the stub right away instead of waiting |
| **M1 Minimum, end to end** | the shortest flow that shows the product working, on the real setup | a working slice beats perfect parts; nobody starts M2 while an M1 item is open |
| **M2 Expert-grade** | depth, polish, fallbacks, test data | only on top of a running M1 |
| **M3 Freeze** | bug fixes only | the demo must run without luck |

After M1, a breaking contract change needs a human `DECISION`.

## A typical exchange

```
frontend → backend   NEED      Need POST /sessions returning {id}. Why: login screen. By M0. Meanwhile I mock it.
backend  → frontend  ACK       ETA 20 min.
backend  → frontend,lead  CONTRACT  backend/CONTRACT.md v1 (a1b2c3d): POST /sessions, GET /sessions/{id}.
backend  → frontend,lead  DONE      Stub on :8000 (d4e5f6a). Run: cd backend && uv run app. Check: curl :8000/health
lead     → backend   BLOCKED   `cd backend && uv run pytest` fails on d4e5f6a: ImportError in app.py:3. Repro: fresh clone.
backend  → lead      DONE      Fixed (e7f8a9b), 12 tests pass.
lead     → humans    DECISION  Deadline unknown. Options: A) freeze at 12:00, B) at 14:00. Recommend A. Blocks: nothing yet.
human (in the issue) [lead] go with A
```

## Why it is built this way

Lessons from the two projects, already built into the rules and tools:

- **One channel, typed messages.** A pinned issue is free, needs no extra service, keeps the whole history, and every agent that can run `gh` can use it. Types tell the recipient what it must do (`ACK` a `NEED` at once, handle `BLOCKED` first) and which messages can wait (`ACK` and `FYI` never wake anyone).
- **Address roles, not people.** One human often runs several agents. A hidden marker in each comment carries the roles, so `wait` wakes only the agent addressed.
- **No @-mentions.** The first version tagged logins. Every tag emailed the person and re-subscribed them to the whole board, so humans drowned in mail. Now agents never tag anyone. A `DECISION` wakes every agent, and each one tells its own human in the chat. Humans reply in the issue with `[role]`, which wakes that agent without an email.
- **Ownership by path, enforced.** "Please stay in your folder" in a prompt is not enough. Agents fix "just one line" elsewhere and cause merge pain. The hook makes the rule hold. `NEED` is the way to get a change in someone else's folder.
- **Contracts and stubs first.** Agents waiting on each other is the main way time gets lost. A contract plus a stub at M0 lets everyone build in parallel against mocks.
- **Push before you announce.** A `DONE` without a pushed commit SHA wastes the consumer's time. Every `DONE` names the SHA and how to verify it.
- **Someone checks every delivery.** lead (or qa) pulls and runs the role's commands after each `DONE` and reports failures as `BLOCKED` with the command, error and SHA. Agents' "it works" is not evidence.
- **Never idle without `wait`.** An agent that stops is invisible. The loop ends in `board wait` (a background command for Claude Code, a foreground loop with a timeout for others), so a message always wakes someone.
- **`STATUS.md` is the memory.** Context runs out. A fresh session resumes from the backlog, the published list and the decisions in `STATUS.md`.
- **Humans decide only what is theirs.** A short list of `DECISION` topics: contracts after M1, scope, privacy, money, destructive git, outside questions. Everything else is decided by lead or the owner and recorded in one line. A reversible decision nobody answers within 30 minutes takes the recommended option, so agents do not stall.
- **The demo runs without luck.** `main` always runs, and every external API has a no-key fallback. Live demos fail on network and quota, not on code.

## Adapting it

- **Solo developer, several agents:** put your login on every role line. The board still routes by role, and each agent still has its own clone.
- **No lead agent:** make lead a human session (it still owns the shared files) and add a `qa` role that verifies.
- **Branches and PRs instead of pushing to `main`:** change `AGENTS.md` → Git. The board flow stays the same. `DONE` then links the PR, and lead or qa reviews it.
- **More message types:** add them to `TYPES` in `board.py` and to the table in `AGENTS.md`. Add a type to `QUIET` if it should not wake anyone.
- **Claude Code permissions:** [.claude/settings.json](../.claude/settings.json) pre-approves the board and read-only git commands. Add `git add`, `git commit` and `git push` there if your team wants a loop that never stops to ask.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `pre-commit: set this clone's role first` | `git config team.role <role>`; the role must be in `tools/team.conf` |
| `pre-commit: role 'x' may only commit inside ...` | unstage the listed files (`git restore --staged <file>`) and post a `NEED` to their owner |
| `board: gh is logged in as X, who is not in tools/team.conf` | `gh auth login` as your own user, or ask lead to add your login |
| `board: git config team.role is ...` | your login runs several roles; set the one this clone is for |
| `wait` never wakes | `ACK` and `FYI` do not wake anyone; an `FYI` without `--to` goes to nobody's inbox; check the sender used your role in `--to` (`board log`) |
| `gh repo view` fails (several remotes) | `gh repo set-default`, or set `repo = owner/name` in `tools/team.conf` |
| Codex cannot reach the board or push | trust the project so `.codex/config.toml` applies (network on); commits need `codex --sandbox danger-full-access` or a human terminal |
| Hook fails on Windows with `\r` errors | `.gitattributes` keeps the hook on LF line endings; a clone made before it: `rm tools/hooks/pre-commit && git checkout -- tools/hooks/pre-commit` |
