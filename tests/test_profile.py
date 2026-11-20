"""Generate the organization profile in fixture consumers and run each tool on them."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_URL = "https://github.com/mathematic-inc/toolconfig-config.git"
CONSUMER_SOURCE = """\
amends "package://github.com/mathematic-inc/toolconfig/releases/download/v2026.11.4/toolconfig@2026.11.4#/ToolConfig.pkl"

root = true

toolconfig {{
  `extends` = List(new Repository {{
    git = "{git}"
    rev = "{rev}"
    path = "profiles/org/.toolconfig.pkl"
  }})
}}
"""

RUST_FILES = {
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

TYPESCRIPT_FILES = {
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

PROTOBUF_FILES = {
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

SHELL_FILES = {
    "greet.sh": """\
#!/usr/bin/env bash
set -euo pipefail

greet() {
  printf 'Hello, %s.\\n' "$1"
}

greet "${1:-world}"
""",
}

DOCKER_AND_WORKFLOW_FILES = {
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

PINACT_CHECK = ("pinact", "run", "--fix=false", "--no-api", ".github/workflows/check.yml")


class Profile(unittest.TestCase):
    environment: dict[str, str]
    revision: str

    @classmethod
    def setUpClass(cls) -> None:
        policy_directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(policy_directory.cleanup)
        policy = Path(policy_directory.name)
        repository = policy / "repository"
        shutil.copytree(ROOT / "profiles", repository / "profiles")
        cls.environment = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": str(policy / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "TOOLCONFIG_REPO_CACHE_DIR": str(policy / "cache"),
        }
        git = ("git", "-C", str(repository))
        cls.run_in(policy, *git, "init", "--quiet")
        cls.run_in(policy, *git, "add", "--all")
        cls.run_in(
            policy,
            *git,
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.com",
            "commit",
            "--quiet",
            "--message=fixture",
        )
        cls.revision = cls.run_in(policy, *git, "rev-parse", "HEAD").stdout.strip()
        # The consumers fetch the profile from this commit, as they fetch it from GitHub.
        cls.run_in(
            policy,
            "git",
            "config",
            "--file",
            str(policy / "gitconfig"),
            f"url.{repository.as_uri()}.insteadOf",
            POLICY_URL,
        )

    @classmethod
    def run_in(cls, directory: Path, *command: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            command,
            cwd=directory,
            env=cls.environment,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"{command}\n{result.stdout}\n{result.stderr}")
        return result

    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        # jactionlint and other tools find their settings at the root of a Git repository.
        self.assert_passes("git", "init", "--quiet")

    def assert_passes(self, *command: str) -> None:
        self.run_in(self.directory, *command)

    def generate_consumer(self, files: dict[str, str]) -> None:
        for name, text in files.items():
            path = self.directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (self.directory / ".toolconfig.pkl").write_text(
            CONSUMER_SOURCE.format(git=POLICY_URL, rev=self.revision), encoding="utf-8"
        )
        self.assert_passes("toolconfig", "generate", "--strict")

    def test_rust(self) -> None:
        self.generate_consumer(RUST_FILES)
        self.assert_passes("cargo", "generate-lockfile", "--offline")
        self.assert_passes("cargo", "fmt", "--check")
        self.assert_passes("cargo-deny", "--locked", "check", "bans", "licenses", "sources")

    def test_typescript(self) -> None:
        self.generate_consumer(TYPESCRIPT_FILES)
        self.assert_passes("oxfmt", "--check", ".")
        self.assert_passes("oxlint", ".")
        self.assert_passes("knip", "--no-progress")

    def test_protobuf(self) -> None:
        self.generate_consumer(PROTOBUF_FILES)
        self.assert_passes("buf", "lint")
        self.assert_passes("buf", "format", "--diff", "--exit-code")

    def test_shell(self) -> None:
        self.generate_consumer(SHELL_FILES)
        self.assert_passes("shellcheck", "greet.sh")
        self.assert_passes("shfmt", "--diff", "greet.sh")

    def test_dockerfile_and_workflow(self) -> None:
        self.generate_consumer(DOCKER_AND_WORKFLOW_FILES)
        self.assert_passes("hadolint", "Dockerfile")
        self.assert_passes(*PINACT_CHECK)


if __name__ == "__main__":
    unittest.main()
