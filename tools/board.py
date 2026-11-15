#!/usr/bin/env python3
"""Agent message board: one pinned GitHub issue the team's agents talk through.

Agents are addressed by ROLE. One GitHub login may run several agents, each in its own clone with
its own `git config team.role`. Roles, logins and the board issue number live in tools/team.conf.

Usage (rules: AGENTS.md -> "The message board"):
  python3 tools/board.py whoami
  python3 tools/board.py post --to <role> --type NEED "text"   (--file msg.md for long text, "-" for stdin)
  python3 tools/board.py inbox [--peek]
  python3 tools/board.py wait [--interval 30] [--timeout 540]
  python3 tools/board.py log [-n 20]
  python3 tools/board.py init                                   (once per project: create and pin the board)

Needs only the Python stdlib and an authenticated `gh` CLI.
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "tools" / "team.conf"
CURSOR_DIR = ROOT / ".board"  # per-clone read cursors (gitignored)
TITLE = "Agent message board"
TYPES = ["NEED", "DONE", "CONTRACT", "BLOCKED", "ACK", "FYI", "DECISION"]
QUIET = {"ACK", "FYI"}  # never wake an agent's `wait`; DECISION wakes all, so each agent tells its human
MARKER = re.compile(r"<!--\s*board\s+(.*?)\s*-->", re.S)


def load_conf(path: Path = CONF) -> tuple[dict[str, str], dict[str, str], dict[str, list[str]]]:
    """team.conf -> (settings, role -> login, role -> path prefixes the role may commit)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        sys.exit(f"board: {path} not found.")
    settings: dict[str, str] = {}
    logins: dict[str, str] = {}
    paths: dict[str, list[str]] = {}
    for n, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" in line:
            key, value = (s.strip() for s in line.split("=", 1))
            settings[key] = value
            continue
        parts = line.split()
        if len(parts) < 3:
            sys.exit(f"board: {path.name}:{n}: expected '<role> <github-login> <paths...>', got '{line}'")
        logins[parts[0]], paths[parts[0]] = parts[1], parts[2:]
    if not logins:
        sys.exit(f"board: {path.name} lists no roles.")
    return settings, logins, paths


SETTINGS, ROLES, PATHS = load_conf()
LOGINS = list(dict.fromkeys(ROLES.values()))


def gh(*args: str, stdin: str | None = None, check: bool = True) -> str | None:
    """Run gh and return its stdout. On failure: exit, or return None when check=False."""
    try:
        r = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    except FileNotFoundError:
        sys.exit("board: the GitHub CLI `gh` is not installed (https://cli.github.com).")
    if r.returncode != 0:
        if not check:
            return None
        sys.exit(f"board: gh {' '.join(args[:2])} failed: {r.stderr.strip()}")
    return r.stdout


@functools.cache
def repo() -> str:
    """owner/name: `repo =` in team.conf, else the GitHub repo of this clone."""
    return SETTINGS.get("repo") or gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner").strip()


def board_issue() -> int:
    value = SETTINGS.get("board", "")
    if not value.isdigit():
        sys.exit("board: no `board = <issue number>` in tools/team.conf. Run: python3 tools/board.py init")
    return int(value)


def canon_login(name: str) -> str | None:
    return {lg.lower(): lg for lg in LOGINS}.get(name.lstrip("@").lower())


def roles_of(login: str) -> list[str]:
    return [r for r, lg in ROLES.items() if lg.lower() == login.lower()]


def me() -> tuple[str, str]:
    """(login, role) of this clone's agent."""
    raw = gh("api", "user", "--jq", ".login").strip()
    login = canon_login(raw)
    if not login:
        sys.exit(f"board: gh is logged in as {raw}, who is not in tools/team.conf ({', '.join(LOGINS)}).")
    role = subprocess.run(["git", "config", "team.role"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    mine = roles_of(login)
    if not role and len(mine) == 1:
        role = mine[0]
    if role not in mine:
        sys.exit(f"board: `git config team.role` is '{role or 'unset'}', but {login} runs {mine}. "
                 f"Run: git config team.role <{'|'.join(mine)}>")
    return login, role


def resolve(to: str, my_role: str) -> list[str]:
    """--to value -> list of roles."""
    out: list[str] = []
    for part in (p.strip() for p in to.split(",") if p.strip()):
        key = part.lstrip("@").lower()
        if key == "all":
            out += [r for r in ROLES if r != my_role]
        elif key == "humans":
            out += list(ROLES)
        elif key in ROLES:
            out.append(key)
        elif canon_login(key):
            out += [r for r in roles_of(canon_login(key)) if r != my_role]
        else:
            sys.exit(f"board: unknown recipient '{part}'. Use a role {list(ROLES)}, a login, 'all' or 'humans'.")
    return list(dict.fromkeys(out))


def fetch(since: str | None = None) -> list[dict]:
    path = f"repos/{repo()}/issues/{board_issue()}/comments?per_page=100"
    if since:
        path += f"&since={since}"
    jq = ".[] | {id, created_at, url: .html_url, author: .user.login, body}"
    out = gh("api", path, "--paginate", "--jq", jq)
    return sorted((json.loads(line) for line in out.splitlines() if line.strip()), key=lambda c: c["id"])


def parse(c: dict) -> dict:
    """Turn a raw comment into a message: sender role, recipient roles, type, text."""
    body = c["body"] or ""
    m = MARKER.search(body)
    if m:
        meta = dict(kv.split("=", 1) for kv in m.group(1).split() if "=" in kv)
        sender = meta.get("from", "?")
        to = [t for t in meta.get("to", "").split(",") if t in ROLES]
        typ = meta.get("type", "FYI").upper()
        text = body[m.end():].strip()
        text = text.split("\n", 1)[1].strip() if text.startswith("**`") and "\n" in text else text
        return {**c, "from_role": sender, "to": to, "type": typ, "text": text, "agent": True}
    # A human wrote in the issue directly: `[role]` tags pick roles (no email); else route by @mentions.
    bracketed = [r for r in ROLES if re.search(rf"\[{re.escape(r)}\]", body, re.I)]
    tagged = [lg for lg in LOGINS if re.search(rf"@{re.escape(lg)}\b", body, re.I)]
    to = bracketed or [r for lg in tagged for r in roles_of(lg)]
    return {**c, "from_role": None, "to": to, "type": "HUMAN", "text": body.strip(), "agent": False}


def for_me(msg: dict, role: str) -> bool:
    if not canon_login(msg["author"]):
        return False  # only the team can address agents
    if msg["agent"] and msg["from_role"] == role:
        return False  # my own posts
    return role in msg["to"]


def show(msg: dict) -> str:
    who = f"{msg['from_role']} agent ({msg['author']})" if msg["agent"] else f"human {msg['author']}"
    to = ", ".join(msg["to"]) or "-"
    when = msg["created_at"].replace("T", " ")[:16]
    return f"--- {msg['type']} from {who} to {to} · {when} UTC · {msg['url']}\n{msg['text']}\n"


def load_cursor(role: str) -> dict:
    try:
        return json.loads((CURSOR_DIR / f"{role}.json").read_text())
    except (OSError, ValueError):
        return {"last_id": 0, "since": None}


def save_cursor(role: str, comments: list[dict], cur: dict) -> None:
    if not comments:
        return
    last = max(comments, key=lambda c: c["id"])
    if last["id"] <= cur["last_id"]:
        return
    CURSOR_DIR.mkdir(exist_ok=True)
    (CURSOR_DIR / f"{role}.json").write_text(json.dumps({"last_id": last["id"], "since": last["created_at"]}))


def unread(role: str) -> tuple[list[dict], list[dict], dict]:
    cur = load_cursor(role)
    new = [c for c in fetch(cur["since"]) if c["id"] > cur["last_id"]]
    return new, [m for m in map(parse, new) if for_me(m, role)], cur


def message_body(typ: str, role: str, to: list[str], text: str) -> str:
    """The comment text. No @-tags: a mention emails that person and re-subscribes them to the whole board.
    Agents are routed by the hidden marker; a DECISION reaches the humans through their own agents."""
    targets = "humans" if typ == "DECISION" else (", ".join(to) or "board")
    header = f"**`{typ}`** · {role} → {targets}"
    if typ == "DECISION":
        header += f" · _needs a human: reply here and write_ `[{role}]`"
    marker = f"<!-- board v2 from={role} to={','.join(to)} type={typ} -->"
    return f"{marker}\n{header}\n\n{text.strip()}\n"


def cmd_whoami(_: argparse.Namespace) -> None:
    login, role = me()
    n = board_issue()
    issue = json.loads(gh("api", f"repos/{repo()}/issues/{n}", "--jq", "{title, state, url: .html_url}"))
    print(f"login: {login}\nrole:  {role}\nrepo:  {repo()}\nboard: #{n} {issue['title']} ({issue['state']}) {issue['url']}")
    hooks = subprocess.run(["git", "config", "core.hooksPath"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    if hooks != "tools/hooks":
        print("warning: ownership hook not enabled. Run: git config core.hooksPath tools/hooks")


def cmd_post(a: argparse.Namespace) -> None:
    _, role = me()
    typ = a.type.upper()
    text = Path(a.file).read_text(encoding="utf-8") if a.file else " ".join(a.text)
    if text.strip() == "-":
        text = sys.stdin.read()
    if not text.strip():
        sys.exit("board: empty message.")
    to = list(ROLES) if typ == "DECISION" else (resolve(a.to, role) if a.to else [])
    if not to and typ not in {"FYI", "ACK"}:
        sys.exit("board: --to is required for this type.")
    body = message_body(typ, role, to, text)
    res = json.loads(gh("api", "--method", "POST", f"repos/{repo()}/issues/{board_issue()}/comments",
                        "--input", "-", stdin=json.dumps({"body": body})))
    print(f"posted {typ} from {role} to {', '.join(to) or 'board (log only)'}: {res['html_url']}")


def cmd_inbox(a: argparse.Namespace) -> None:
    _, role = me()
    new, msgs, cur = unread(role)
    print("\n".join(map(show, msgs)) if msgs else "inbox: no new messages.")
    if not a.peek:
        save_cursor(role, new, cur)


def cmd_wait(a: argparse.Namespace) -> None:
    login, role = me()
    start = time.time()
    print(f"waiting for messages to {role} ({login}) on #{board_issue()}, every {a.interval}s ...", flush=True)
    while True:
        new, msgs, cur = unread(role)
        if any(m["type"] not in QUIET for m in msgs):
            print("\n".join(map(show, msgs)), flush=True)
            save_cursor(role, new, cur)
            return
        if a.timeout and time.time() - start >= a.timeout:
            print("wait: timed out, no new messages. Run it again.")
            sys.exit(2)
        time.sleep(a.interval)


def cmd_log(a: argparse.Namespace) -> None:
    msgs = [parse(c) for c in fetch()][-a.n:]
    print("\n".join(map(show, msgs)) if msgs else "board is empty.")


BOARD_BODY = """\
This issue is the **message board** for the team's agents. Keep it open and pinned; do not edit or delete other people's comments.

- Agents post and read only through `python3 tools/board.py` (`inbox`, `wait`, `post`, `log`). Rules and message types: [AGENTS.md]({agents_md}).
- The board never @-mentions anyone, so it sends no emails. You may unsubscribe from this issue: your agent tells you in its chat when a `DECISION` needs you.
- Humans can write here directly: put a role in brackets to wake that agent, e.g. `[lead] go with A` (several: `[backend] [frontend] ...`). An `@login` also works, but GitHub then emails that person.

| Role | Run by | Writes in |
|---|---|---|
{rows}

**Message types:** `NEED` (ACK at once, DONE when delivered) · `DONE` (pushed, with SHA and path) · `CONTRACT` (interface changed) · `BLOCKED` (urgent) · `ACK` · `FYI` · `DECISION` (needs a human).
"""


def cmd_init(_: argparse.Namespace) -> None:
    me()  # the caller must be on the team
    current = SETTINGS.get("board", "")
    if current.isdigit():
        found = gh("api", f"repos/{repo()}/issues/{current}", "--jq", "{title, url: .html_url}", check=False)
        if found and json.loads(found)["title"] == TITLE:
            sys.exit(f"board: the board already exists: {json.loads(found)['url']}")
    rows = "\n".join(f"| `{r}` | `{ROLES[r]}` | {', '.join(f'`{p}`' for p in PATHS[r])} |" for r in ROLES)
    agents_md = f"https://github.com/{repo()}/blob/HEAD/AGENTS.md#the-message-board"
    body = BOARD_BODY.format(agents_md=agents_md, rows=rows)
    url = gh("issue", "create", "--repo", repo(), "--title", TITLE, "--body", body).strip().splitlines()[-1]
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    pinned = gh("issue", "pin", str(number), "--repo", repo(), check=False) is not None
    text = CONF.read_text(encoding="utf-8")
    text, n = re.subn(r"(?m)^(\s*board\s*=\s*)\S*", rf"\g<1>{number}", text, count=1)
    CONF.write_text(text if n else text.rstrip("\n") + f"\nboard = {number}\n", encoding="utf-8")
    print(f"created the board: {url}" + ("" if pinned else "\nwarning: could not pin it (needs admin rights); pin it by hand"))
    print(f"tools/team.conf now says `board = {number}`. Commit it as lead: git add tools/team.conf && git commit -m 'lead: board'")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="Agent message board (pinned issue).")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami", help="show login, role and board").set_defaults(fn=cmd_whoami)
    s = sub.add_parser("post", help="post a message")
    s.add_argument("--to", help="role(s), login(s), 'all' or 'humans', comma-separated")
    s.add_argument("--type", required=True, type=str.upper, choices=TYPES)
    s.add_argument("--file", help="read the message text from a file")
    s.add_argument("text", nargs="*", help="message text, or '-' for stdin")
    s.set_defaults(fn=cmd_post)
    s = sub.add_parser("inbox", help="print unread messages for me and mark them read")
    s.add_argument("--peek", action="store_true", help="do not mark as read")
    s.set_defaults(fn=cmd_inbox)
    s = sub.add_parser("wait", help="block until a message for me arrives")
    s.add_argument("--interval", type=int, default=30, help="seconds between polls (default 30)")
    s.add_argument("--timeout", type=int, default=0, help="give up after N seconds, exit code 2 (default: never)")
    s.set_defaults(fn=cmd_wait)
    s = sub.add_parser("log", help="recent board history")
    s.add_argument("-n", type=int, default=20)
    s.set_defaults(fn=cmd_log)
    sub.add_parser("init", help="once per project: create and pin the board issue").set_defaults(fn=cmd_init)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
