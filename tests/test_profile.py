"""Generate the organization profile in fixture consumers and run each tool on them."""

import json
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles" / "org" / ".toolconfig.pkl"

RUST = {
    "Cargo.toml": """\
[package]
name = "fixture"
version = "2026.11.0"
edition = "2024"
license = "MIT"
publish = false
""",
    "src/lib.rs": """\
/// Returns the sum of two numbers.
#[must_use]
pub const fn add(left: u64, right: u64) -> u64 {
    left + right
}
""",
}

TYPESCRIPT = {
    "package.json": """\
{
  "name": "fixture",
  "version": "2026.11.0",
  "private": true,
  "type": "module",
  "exports": "./src/index.ts"
}
""",
    "tsconfig.json": """\
{
  "compilerOptions": {
    "module": "nodenext",
    "strict": true,
    "target": "es2024"
  },
  "include": ["src"]
}
""",
    "src/index.ts": """\
export function greet(name: string): string {
  return `Hello, ${name}.`;
}
""",
}

PYTHON = {
    "fixture.py": '''\
"""A module that the fixture checks."""


def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}."
''',
}

PROTOBUF = {
    "acme/v1/greeting.proto": """\
syntax = "proto3";

package acme.v1;

service GreetingService {
  rpc Greet(GreetRequest) returns (GreetResponse);
}

message GreetRequest {
  string name = 1;
}

message GreetResponse {
  string greeting = 1;
}
""",
}

SHELL = {
    "greet.sh": """\
#!/usr/bin/env bash
set -euo pipefail

greet() {
\tprintf 'Hello, %s.\\n' "$1"
}

greet "${1:-world}"
""",
}

DOCUMENTS = {
    "README.md": """\
# Fixture

The [guide](docs/guide.md) shows how to use the fixture.
""",
    "docs/guide.md": """\
# Guide

Run the checks before you push a change.
""",
    "config.yaml": """\
name: fixture
enabled: true
items:
  - one
  - two
""",
    "settings.toml": """\
name = "fixture"
items = ["one", "two"]
""",
    "Dockerfile": """\
FROM debian:13-slim
USER 65534
""",
    ".github/workflows/check.yml": """\
name: Check

on:
  pull_request:

permissions: {}

jobs:
  check:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: dtolnay/rust-toolchain@b725eda525362e7cf34af9a7243cac1e3f01a7ec # stable
      - run: cargo test
""",
}

PINACT = ("pinact", "run", "--fix=false", "--no-api", ".github/workflows/check.yml")


class Profile(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(shutil.which("toolconfig"), "Install the pinned tools first")
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        # jactionlint and other tools find their settings at the root of a Git repository.
        self.assert_passes("git", "init", "--quiet")

    def run_tool(self, *command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=self.directory,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )

    def assert_passes(self, *command: str) -> None:
        result = self.run_tool(*command)
        self.assertEqual(result.returncode, 0, f"{command}\n{result.stdout}\n{result.stderr}")

    def consumer(self, files: dict[str, str], overrides: str = "") -> None:
        for name, text in files.items():
            path = self.directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (self.directory / ".toolconfig.pkl").write_text(
            f"amends {json.dumps(str(PROFILE))}\n{overrides}\n", encoding="utf-8"
        )
        self.assert_passes("toolconfig", "generate", "--strict")
        self.assert_passes("toolconfig", "check", "--strict")

    def read_json(self, name: str) -> dict:
        return json.loads((self.directory / name).read_text(encoding="utf-8"))

    def read_toml(self, name: str) -> dict:
        return tomllib.loads((self.directory / name).read_text(encoding="utf-8"))

    def test_settings(self) -> None:
        self.consumer({})
        deny = self.read_toml("deny.toml")
        self.assertEqual(deny["licenses"]["allow"], ["Apache-2.0", "MIT", "Unicode-3.0", "Zlib"])
        self.assertEqual(deny["bans"]["wildcards"], "deny")
        self.assertEqual(deny["sources"]["unknown-git"], "deny")
        oxlint = self.read_json(".oxlintrc.json")
        self.assertTrue(oxlint["options"]["typeAware"])
        self.assertEqual(oxlint["categories"]["pedantic"], "deny")
        self.assertEqual(self.read_toml(".rumdl.toml")["MD013"]["line-length"], 80)
        self.assertEqual(self.read_toml("rustfmt.toml")["max_width"], 100)
        self.assertEqual(self.read_toml(".ryl.toml")["lint"]["rules"]["line-length"], "disable")
        self.assertNotIn("line-width", self.read_toml("tombi.toml")["format"]["rules"])
        self.assertIn("CHANGELOG.md", self.read_toml("typos.toml")["files"]["extend-exclude"])
        editorconfig = (self.directory / ".editorconfig").read_text(encoding="utf-8")
        self.assertIn("[*.go]\nindent_style = tab\n", editorconfig)
        self.assertIn("[*.{sh,bash}]\nindent_style = tab\n", editorconfig)

    def test_rust(self) -> None:
        self.consumer(RUST)
        self.assert_passes("cargo", "generate-lockfile", "--offline")
        self.assert_passes("cargo", "fmt", "--check")
        self.assert_passes("cargo-deny", "--locked", "check", "bans", "licenses", "sources")

    def test_typescript(self) -> None:
        self.consumer(TYPESCRIPT)
        self.assert_passes("oxfmt", "--check", ".")
        self.assert_passes("oxlint", ".")
        self.assert_passes("knip", "--no-progress")

    def test_python(self) -> None:
        self.consumer(PYTHON)
        self.assert_passes("ruff", "check", ".")
        self.assert_passes("ruff", "format", "--check", ".")
        self.assert_passes("ty", "check", ".")

    def test_protobuf(self) -> None:
        self.consumer(PROTOBUF)
        self.assert_passes("buf", "lint")
        self.assert_passes("buf", "format", "--diff", "--exit-code")

    def test_shell(self) -> None:
        self.consumer(SHELL)
        self.assert_passes("shellcheck", "greet.sh")
        self.assert_passes("shfmt", "--diff", "greet.sh")

    def test_documents(self) -> None:
        self.consumer(DOCUMENTS)
        self.assert_passes("rumdl", "check", ".")
        self.assert_passes("ryl", "check", "--strict", ".")
        self.assert_passes("tombi", "format", "--check", "settings.toml")
        self.assert_passes("tombi", "lint", "settings.toml")
        self.assert_passes("typos", ".")
        self.assert_passes("lychee", "README.md", "docs/guide.md")
        self.assert_passes("gitleaks", "dir", "--redact", "--no-banner", ".")
        self.assert_passes("hadolint", "Dockerfile")
        self.assert_passes("jactionlint", ".github/workflows/check.yml")
        self.assert_passes(*PINACT)

    def test_pinact_needs_policy(self) -> None:
        self.consumer(DOCUMENTS)
        (self.directory / ".pinact.yaml").unlink()
        result = self.run_tool(*PINACT)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires a version comment", result.stdout + result.stderr)

    def test_local_exception(self) -> None:
        self.consumer(
            {},
            'sections { ["*"] { oxlint { rules { ["unicorn/prefer-dom-node-dataset"] = "allow" } } } }',
        )
        rules = self.read_json(".oxlintrc.json")["rules"]
        self.assertEqual(rules["unicorn/prefer-dom-node-dataset"], "allow")
        self.assertEqual(rules["curly"], "deny")

    def test_clean_checkout(self) -> None:
        for name in (".toolconfig.pkl", ".toolconfig.lock", ".editorconfig", ".gitignore"):
            shutil.copyfile(ROOT / name, self.directory / name)
        shutil.copytree(ROOT / "profiles", self.directory / "profiles")
        tracked = {
            name: (self.directory / name).read_bytes()
            for name in (".editorconfig", ".toolconfig.lock")
        }
        self.assert_passes("toolconfig", "check", "--strict")
        self.assert_passes("toolconfig", "generate", "--strict")
        for name, content in tracked.items():
            self.assertEqual((self.directory / name).read_bytes(), content, name)


if __name__ == "__main__":
    unittest.main()
