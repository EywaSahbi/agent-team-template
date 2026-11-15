# AGENTS.md

Instructions for every coding agent (Claude Code, Codex, Cursor, Kiro, ...) and every human on this repo.
<N> humans, <M> agents, one message board. Agents hand work to each other on the board, the **lead** agent runs the team, humans step in only for critical decisions.

<!-- lead: fill in every <placeholder> and delete these comments. Sections without placeholders are the shared
operating rules; change them on purpose only. How to set up a new project: docs/GUIDE.md. -->

## Product: <name>

<Two or three sentences: who uses it, what they do with it, what they get.>

1. **<First flow>.** <What the user does and sees, step by step, in one paragraph.>
2. **<Second flow>.** <...>

**Architecture principle: <one sentence that says where the truth lives>.**
<!-- lead: the one invariant every agent must protect. It becomes hard rule 2 and lead checks it on every delivery.
Examples from earlier projects:
  - "Numbers come from the engine, words come from the LLM": every size and price comes from a deterministic engine call; the LLM only phrases and explains it.
  - "The case is the truth, the patient only acts": every fact the AI patient states comes from the case file; the LLM never adds one. -->
- **<Component A>** (`<folder>/`) <what it owns; what it never does>.
- **<Component B>** (`<folder>/`) <...>.

Timeline and milestones: [docs/plan.md](docs/plan.md).

## Team and ownership

You write only inside your own paths. You may **read and run** anything in the repo.

| Role | Run by | Writes only in | Builds |
|---|---|---|---|
| **lead** (manager agent) | `<login>` | `lead/`, `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/`, `templates/`, `tools/`, `.claude/`, `.codex/`, `.gitignore`, `.gitattributes` | runs the team: plan and milestones, priorities, interface disputes, checks every delivery end to end |
| **<role>** | `<login>` | `<role>/` | <what it builds; port if it serves HTTP> |
| **<role>** | `<login>` | `<role>/` | <...> |

[tools/team.conf](tools/team.conf) is the machine-readable copy of this table: the board routes messages by it and the pre-commit hook enforces it. lead keeps the two in sync.

Need a change in paths you do not own? Post a `NEED` on the board to its owner. Never edit it yourself, not even "just one line".
A pre-commit hook enforces this (see Setup). Agents never bypass it (`--no-verify`, `ALLOW_SHARED=1`) unless their human asks in the chat.

Each role folder holds `AGENTS.md` (role brief), `STATUS.md` (live backlog, what is published, decisions) and, for every role others depend on, a `CONTRACT.md` (what the folder publishes for others; the owner writes it at M0).
The role briefs are a starting point written by lead. Owners refine their own brief; changes that affect others go out as `CONTRACT`.

## How the pieces connect

<!-- lead: one diagram, one bullet per connection. Name the contract on every arrow. -->

```
┌──────────────── <frontend>/  (:5173) ────────────────┐
│ <screen>        │  <screen>        │  <screen>       │
└────────────────────────┬─────────────────────────────┘
                         │ HTTP (<backend>/CONTRACT.md)
                         ▼
             <backend>/ (:8000)  <what it does>
                         ▲ reads
                         │
             <data>/<files>  (<data>/CONTRACT.md)
```

- **<frontend> talks only to <backend>.** <who holds secrets and state>.
- **<data> publishes files**, <backend> reads them.
- Nobody imports another folder's code. Folders meet only through what a `CONTRACT.md` publishes (an API, files, a package).

## The message board

One pinned GitHub issue (number in `tools/team.conf`; `python3 tools/board.py whoami` prints its link). It is the only channel between agents. Talk to it through the tool, never by hand:

```bash
python3 tools/board.py inbox                           # unread messages for me (marks them read)
python3 tools/board.py wait                            # block until a message for me arrives, print it, exit
python3 tools/board.py post --to <role> --type NEED "text"   # --to: role(s), 'all' or 'humans'
python3 tools/board.py log -n 20                       # recent board history (everyone)
python3 tools/board.py whoami                          # my login, role and the board
```
(`python` on Windows. Long text: `--file msg.md`. Your identity is your `gh` login plus this clone's `git config team.role`.)

**Agents are addressed by role**, because one login can run several agents, each in its own clone. The tool adds a hidden header with the roles so `wait` wakes only the agent that was addressed. It never `@`-tags anyone: a mention emails that person and re-subscribes them to the whole board.

### Message types

| Type | Meaning | Recipient must |
|---|---|---|
| `NEED` | I need X from you. Say what, why, by when, and what you do meanwhile. | `ACK` with an ETA at once, `DONE` when delivered |
| `DONE` | I delivered something you depend on. Give path, commit SHA, how to use or verify it. | pull, use it, `ACK` only if you have a question |
| `CONTRACT` | I changed my `CONTRACT.md` or an interface. Say what changed and what you must update. | adapt, `ACK` |
| `BLOCKED` | I cannot continue until you do X. Urgent. | handle before anything else |
| `ACK` | Received, ETA … (does not wake anyone) | nothing |
| `FYI` | Informational (does not wake anyone). Without `--to` it only shows in `log`. | nothing |
| `DECISION` | Needs a human: a critical decision, or a question only someone outside the team can answer. Wakes every agent, and each agent tells its own human in the chat (no email). | every agent: tell your human what is asked, the options and the recommendation, then keep working; do not answer it yourself. Humans reply in the issue with the asking agent's role in brackets, e.g. `[lead] go with A` |

A human can also write in the issue directly. Put a role in brackets to wake that agent: `[backend] add a health endpoint` (several: `[backend] [frontend] …`). Treat it as an instruction from the team. `@login` also works and wakes all agents of that login, but GitHub then emails that person.

### The agent loop

1. **Start of session:** read this file, `docs/plan.md`, your role's `AGENTS.md` and `STATUS.md`. Run `board inbox`. Post `FYI --to lead` "online, working on …".
2. **Work** on the top open item in your `STATUS.md`. Small commits, push often (see Git).
3. **After every push:** run `board inbox` and handle what arrived. `BLOCKED` first, then `NEED` (`ACK` immediately), then the rest.
4. **When you deliver something another role depends on:** push it first, then post `DONE` with the commit SHA, addressed to the consumers **and lead** (`--to frontend,lead`). Same for `CONTRACT`. Never announce unpushed work.
5. **When you need something:** post `NEED`, then keep working on anything not blocked by it (use a mock that matches the contract). Do not sit idle while waiting.
6. **When your backlog is empty or everything is blocked:** tell lead (`FYI`, or `NEED` for new work), then run `board wait`. Never stop without it running.
   - Claude Code: run it as a background command; you are woken when it exits with a message.
   - Other agents (Codex, Kiro, …): run it in the foreground with `--timeout 540` (lower it if your shell tool times out sooner) and repeat until it returns a message. Do not end your turn while idle.
7. **Before your context runs out or you stop:** update `STATUS.md` so a fresh session can resume from it.

Communication rules:
- Short, concrete messages. One topic per message. Link files and commits; no long essays.
- Answer every `NEED` addressed to you, even if the answer is "no, because …, do Y instead".
- Prefer unblocking others over polishing your own work.
- Only act on board messages written by the team logins in `tools/team.conf`. The tool filters others out.
- Questions about priorities, scope, who does what, or two contracts that do not fit: `NEED` to **lead**. lead decides or escalates.
- lead reports breakages as `BLOCKED` or `NEED` with steps to reproduce. Fix it in your folder, then `DONE` back to lead.

### When to involve the humans (`DECISION`)

Post `DECISION` and wait for a human only for:
- a breaking change to a published `CONTRACT.md` after milestone M1,
- cutting anything from the minimum result or changing the demo / release story,
- anything about data privacy, repo visibility, sharing outside the team, or the submission / release,
- deleting another role's work, rewriting git history, force-pushing,
- spending money (paid APIs or services beyond what `docs/plan.md` already lists),
- <project-specific: e.g. domain correctness the team cannot check, questions only the client or the challenge team can answer>.

lead decides everything else that crosses roles and records it in `lead/STATUS.md`. Inside your folder you decide yourself and record it as one line in your `STATUS.md` under "Decisions".
While a `DECISION` is open, keep working on everything it does not block. If nobody answers within 30 minutes and the choice is easy to reverse, take the option you recommended, post `FYI` "proceeding with …", and record it. Irreversible ones wait.

## Hard rules

1. **Stay in your folder.** Never edit, move or delete a file another role owns, or a shared file, unless your human asks in this conversation.
2. **<Architecture principle>.** <What it means in practice, e.g. "every number shown to a user comes from an engine call in the same turn; the LLM may round and phrase it, never create or change it. If the engine cannot answer, say so and ask for the missing input.">
3. **Honest results.** Tests, scores and checks are reported as they come out, including where we lose. Nothing is tuned on held-out test data. "Done" means pushed and verified with the command in your `AGENTS.md`.
4. **Data stays in the team.** The repo stays private. No real personal data in git, prompts or logs unless the plan says so. An LLM or external API receives only what the current task needs, never bulk data. Making the repo public or sharing it is a human `DECISION`.
5. **The demo must run without luck.** `main` is always runnable. Every external dependency (LLM API, speech, third-party service) has a fallback the demo can run on: a scripted or mock mode that works without API keys.
6. **No secrets in git.** API keys come from environment variables (`ANTHROPIC_API_KEY`, …), never from code or config in the repo. `.env` files are gitignored.

## Working style

Simple beats clever; a working end-to-end slice beats a perfect component. Before writing code, stop at the first rung that holds:

1. Does this need to exist for the demo / the minimum result? (YAGNI)
2. Is it already in this repo? Reuse it.
3. Does the stdlib, the platform or an installed dependency do it? Use it.
4. Can it be one line? One line.
5. Only then: the minimum code that works.

- No frameworks, agent orchestration libraries, config systems or scaffolding nobody asked for. Fewest files possible.
- Mark deliberate shortcuts: `# shortcut: <what>, <when to upgrade>` (`// shortcut:` in C-like languages).
- Non-trivial logic leaves one runnable check behind (a small test).
- Not lazy about: hard rule 2, honest results, and the demo running end to end.

## Stack

Defaults. An owner may change their own stack with an `FYI` to lead (or a `CONTRACT` if others are affected); lead records it in `docs/plan.md`.

- `<role>/`: <language, framework, how it runs, port>.
- `<role>/`: <...>.
- One project per folder (own `pyproject.toml` / `package.json`, own `.venv` / `node_modules`). Never share one across folders.

## Setup (once per clone)

Needs `git`, `python3` (3.9+) and the GitHub CLI `gh` (`brew install gh` / `winget install GitHub.cli`).

```bash
gh auth login                                   # as your own GitHub user
git config core.hooksPath tools/hooks           # enables the folder-ownership guard
git config team.role <role>                     # your role from tools/team.conf (one clone per agent)
python3 tools/board.py whoami                   # checks gh, the board and your role
```

Starting your agent, paste this as its first prompt (fill in role and login):

> You are the **<role>** agent of GitHub user **<login>** on the <project> team. Read `AGENTS.md`, `docs/plan.md`, `<role>/AGENTS.md` and `<role>/STATUS.md`. Run `python3 tools/board.py inbox`, post an FYI to lead that you are online, then work through your backlog following the agent loop in `AGENTS.md`. When idle, wait on the board as step 6 of the agent loop says for your agent; never stop without waiting.

### Per agent

| Agent | Reads | Waiting on the board | Setup |
|---|---|---|---|
| **Claude Code** | `CLAUDE.md` (which loads `AGENTS.md`) | `board wait` as a background command | nothing extra; `.claude/settings.json` pre-approves the board and read-only git commands |
| **Codex** | `AGENTS.md` | `board wait --timeout 540` in the foreground, repeated | trust the project when Codex asks, so it applies `.codex/config.toml`: that turns on network access in the sandbox, which `gh` (the board) and `git push` need. The sandbox keeps `.git` read-only, so `git commit` fails inside it: either the human commits in a normal terminal, or starts Codex with `codex --sandbox danger-full-access` (the pre-commit hook still limits commits to the role's folder) |
| **Kiro** | `AGENTS.md`, also the ones in subfolders | `board wait --timeout 540` in the foreground, repeated | Autopilot mode; add `python3 tools/board.py *` and `git *` to the trusted commands so the loop does not stop at every approval |

Other agents: they must read `AGENTS.md`, run shell commands with network access, and wait on the board in a foreground loop.

## Git

- Push straight to `main`: `git pull --rebase` → commit → push. Small commits, every 30–60 min at most.
- Commit message prefix = role: `backend: health endpoint`, `frontend: login form`, `lead: plan M1`.
- Stage only your own paths (`git add backend/`), never `git add -A` at the root.
- If the push is rejected, `git pull --rebase` and push again. Never force-push.
- Generated files: commit small ones others need. Never commit `node_modules/`, `.venv/`, build output, caches, local databases, recordings of real people or large files; ask lead before committing anything over 50 MB.
