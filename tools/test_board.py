"""Checks for tools/board.py and tools/hooks/pre-commit (stdlib only, no network).

Run from the repo root:  python3 -m unittest discover tools
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import board  # noqa: E402  (also checks that the shipped team.conf parses)

CONF = """\
# a comment
board = 7          # inline comment
lead   alice  lead/ AGENTS.md docs/
api    alice  api/
web    bob    web/ shared/web-
"""
TEAM = {"ROLES": {"lead": "alice", "api": "alice", "web": "bob"}, "LOGINS": ["alice", "bob"]}


def comment(body: str, author: str = "alice") -> dict:
    return {"id": 1, "created_at": "2026-01-01T10:00:00Z", "url": "u", "author": author, "body": body}


class ConfTest(unittest.TestCase):
    def test_parses_settings_roles_and_paths(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "team.conf"
            p.write_text(CONF)
            settings, roles, paths = board.load_conf(p)
        self.assertEqual(settings, {"board": "7"})
        self.assertEqual(roles, TEAM["ROLES"])
        self.assertEqual(paths["web"], ["web/", "shared/web-"])

    def test_role_line_without_paths_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "team.conf"
            p.write_text("api alice\n")
            with self.assertRaises(SystemExit):
                board.load_conf(p)


@mock.patch.multiple(board, **TEAM)
class RoutingTest(unittest.TestCase):
    def test_resolve(self):
        self.assertEqual(board.resolve("all", "api"), ["lead", "web"])
        self.assertEqual(board.resolve("humans", "api"), ["lead", "api", "web"])
        self.assertEqual(board.resolve("@Bob, lead", "api"), ["web", "lead"])
        self.assertEqual(board.resolve("alice", "api"), ["lead"])  # a login means its other agents
        with self.assertRaises(SystemExit):
            board.resolve("nobody", "api")

    def test_agent_message_round_trip(self):
        body = board.message_body("NEED", "api", ["web", "lead"], "  need the login form  ")
        self.assertNotIn("@", body)  # never mentions anyone, so GitHub sends no email
        msg = board.parse(comment(body))
        self.assertEqual((msg["from_role"], msg["to"], msg["type"], msg["text"]),
                         ("api", ["web", "lead"], "NEED", "need the login form"))
        self.assertTrue(board.for_me(msg, "web"))
        self.assertFalse(board.for_me(msg, "api"))  # my own post

    def test_decision_reaches_every_agent(self):
        body = board.message_body("DECISION", "web", list(board.ROLES), "A or B?")
        self.assertIn("`[web]`", body)
        self.assertEqual(board.parse(comment(body, "bob"))["to"], ["lead", "api", "web"])

    def test_human_message_routing(self):
        self.assertEqual(board.parse(comment("[API] please add X"))["to"], ["api"])
        self.assertEqual(board.parse(comment("[lead] [web] go with A"))["to"], ["lead", "web"])
        self.assertEqual(board.parse(comment("@bob can you look"))["to"], ["web"])
        self.assertEqual(board.parse(comment("@ALICE hi"))["to"], ["lead", "api"])
        self.assertEqual(board.parse(comment("[api] bracket wins over @bob"))["to"], ["api"])
        self.assertEqual(board.parse(comment("no address"))["to"], [])

    def test_outsiders_cannot_address_agents(self):
        self.assertFalse(board.for_me(board.parse(comment("[api] do it", author="stranger")), "api"))


class HookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q")
        (self.repo / "tools").mkdir()
        (self.repo / "tools" / "team.conf").write_text(CONF.replace("\n", "\r\n"))  # CRLF must work too

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)

    def commit_ok(self, role: str | None, *files: str, env: dict | None = None) -> bool:
        if role:
            self.git("config", "team.role", role)
        for f in files:
            (self.repo / f).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / f).write_text("x")
            self.git("add", f)
        hook = TOOLS / "hooks" / "pre-commit"
        r = subprocess.run(["sh", str(hook)], cwd=self.repo, capture_output=True, env={**os.environ, **(env or {})})
        return r.returncode == 0

    def test_own_folder_passes(self):
        self.assertTrue(self.commit_ok("web", "web/app.ts"))

    def test_file_prefix_passes(self):
        self.assertTrue(self.commit_ok("web", "shared/web-theme.css"))

    def test_lead_root_file_passes(self):
        self.assertTrue(self.commit_ok("lead", "AGENTS.md", "docs/plan.md"))

    def test_other_folder_fails(self):
        self.assertFalse(self.commit_ok("web", "web/app.ts", "api/server.py"))

    def test_no_role_fails(self):
        self.assertFalse(self.commit_ok(None, "web/app.ts"))

    def test_unknown_role_fails(self):
        self.assertFalse(self.commit_ok("nobody", "web/app.ts"))

    def test_allow_shared_bypasses(self):
        self.assertTrue(self.commit_ok("web", "api/server.py", env={"ALLOW_SHARED": "1"}))


if __name__ == "__main__":
    unittest.main()
