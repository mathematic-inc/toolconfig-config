# ToolConfig policy for mathematic-inc

The shared [ToolConfig](https://github.com/mathematic-inc/toolconfig) policy for
the repositories of mathematic-inc. It needs ToolConfig 2026.11.4 or newer and
Git.

The policy is one profile, `profiles/org/.toolconfig.pkl`. It holds the settings
that ToolConfig writes for the tools of mathematic-inc repositories.
[Outside ToolConfig](#outside-toolconfig) gives the other settings. Where
repositories disagree, the profile keeps the stricter setting. For a pure style
choice, it keeps the most common one. [Decisions](#decisions) gives each choice
and its reason.

## Import

Write this `.toolconfig.pkl` in the repository:

```pkl
amends "package://github.com/mathematic-inc/toolconfig/releases/download/v2026.11.4/toolconfig@2026.11.4#/ToolConfig.pkl"

root = true

toolconfig {
  `extends` = List(new Repository {
    git = "https://github.com/mathematic-inc/toolconfig-config.git"
    rev = "REPLACE_WITH_FULL_COMMIT_ID"
    path = "profiles/org/.toolconfig.pkl"
  })
}
```

A TOML source uses the same `git`, `rev` and `path` in `[toolconfig].extends`.
Use a full commit ID, never a branch or a tag.

Keep only these settings in the repository:

- Paths, such as the `modules` of `buf.yaml`.
- Exclusions of generated, vendored and built folders.
- Word lists for typos.
- Exceptions, each with a comment that gives its reason.

Local tables merge with the profile key by key. A local list replaces the list
of the profile. Thus, a local `ignorePatterns` or `extend-exclude` list must
repeat the entries of the profile that it keeps. A local `files` entry, such as
`ryl` or `pinact`, replaces the whole entry of the profile. Copy the full entry
to change one value.

Remove each native file that the profile writes with `git rm` before the first
`toolconfig generate`. ToolConfig does not overwrite a file that it did not
write. Then run `toolconfig init --gitignore`, so that Git ignores the generated
files. Commit `.toolconfig.pkl`, `.toolconfig.lock`, `.editorconfig` and
`.gitignore`.

A fresh checkout does not have the generated files. In `hk.pkl`, copy the
`toolconfig` step of this repository as the first step. In CI, run
[toolconfig-action](https://github.com/mathematic-inc/toolconfig-action) in each
job that runs a tool, before that tool. The action runs
`toolconfig check --strict` and then `toolconfig generate --strict`. A job that
runs only `hk check` can run `toolconfig check --strict` before hk instead. The
first hk step then generates the files.

## What the profile writes

Run `toolconfig list` to see the files that the profile writes. Run
`toolconfig explain` to see each value and its source.

Type-aware oxlint rules need `oxlint-tsgolint`. oxfmt stops with an error on a
`.svelte` file when `svelte` is not in the `node_modules` folder of that oxfmt.
A repository with `.svelte` files runs oxfmt from `node_modules`, with `svelte`
installed.

## Outside ToolConfig

These settings are not in a file that ToolConfig writes.

`hk.pkl` in this repository has the steps of the organization. The harper,
zizmor, gitleaks and kingfisher steps hold their settings as command-line
options. ghalint, shellharden and sort-package-json run with their defaults. The
harper step ignores only the rules that every repository ignores. The zizmor
step reports findings of every severity. The jactionlint step takes its profile
from `.github/actionlint.yaml`, so it has no `--profile` option.

Clippy reads its lint levels from `Cargo.toml`, which ToolConfig does not write.
Put this table in the root `Cargo.toml` of each Rust repository. Add
`[lints] workspace = true` to each crate of the workspace. A single crate with
no workspace uses `[lints.clippy]` and `[lints.rust]`.

```toml
[workspace.lints.clippy]
all = { level = "deny", priority = -1 }
nursery = { level = "deny", priority = -1 }
pedantic = { level = "deny", priority = -1 }
redundant_pub_crate = "allow"

[workspace.lints.rust]
missing_debug_implementations = "deny"
missing_docs = "deny"
rust_2018_idioms = { level = "deny", priority = -1 }
unreachable_pub = "deny"
```

## Decisions

The values come from the settings files, `hk.pkl` steps and CI commands of 22
repositories on 2026-11-20. "Default" means that the repository runs the tool
with no setting.

| Setting | Values seen | Choice | Reason |
| --- | --- | --- | --- |
| Markdown line length (rumdl MD013) | Off: claude-tools-mcp, connectrpc-tauri, if-changed, mcpr, smapped-traces, sqlc-gen-sqlx, tauri-plugin-ui-inspector, ts-japi, unfmt, vscode-api-linter, vscode-latex, vscode-pdf. On at 80: addr-spec-rs, alyt, connectrpc-sdk, noop, protovalidate-buffa | on at 80 | Stricter: a rule on and the lower limit |
| rumdl MD024, MD033, MD036, MD057 | Off: vscode-api-linter (MD024, MD033), ts-japi (MD033), alyt `docs/plans` (MD036), smapped-traces and sqlc-gen-sqlx (MD057). On: others | on | Stricter |
| Trailing whitespace in Markdown | Kept: toolconfig. Removed: the 18 repositories with hk | removed | Stricter |
| oxlint categories | `correctness`, `suspicious`, `pedantic` and `perf` `deny`: 9 repositories. `correctness` `error`: bucket-cache-action | all four `deny` | Stricter |
| oxlint type-aware rules | On: bucket-cache-action, ts-japi (`no-deprecated` only). Off: 8 repositories | on | Stricter |
| oxlint unused disable directives | `deny`: 9 repositories. Default: bucket-cache-action | `deny` | Stricter |
| oxlint `require-unicode-regexp` flag | `v`: connectrpc-sdk, connectrpc-tauri, smapped-traces, ts-japi, vscode-api-linter, vscode-latex and tauri-plugin-ui-inspector apps. `u`: alyt, vscode-pdf, tauri-plugin-ui-inspector `packages` | `v` | Stricter: the `v` flag rejects more patterns. Most repositories use it |
| oxlint `unicorn/require-post-message-target-origin`, `unicorn/prefer-dom-node-dataset` | `allow`: vscode-pdf, tauri-plugin-ui-inspector. `deny` through the suspicious and pedantic categories: others | `deny` | Stricter. An exception stays local, with its reason |
| oxfmt `sortImports` | On: 9 repositories. Default (off): bucket-cache-action | on | Stricter |
| oxfmt `sortPackageJson` | Off: 9 repositories. Default (on): bucket-cache-action | off | sort-package-json sorts `package.json` in the hk repositories, and the two orders differ. 9 of 10 repositories turn `sortPackageJson` off |
| oxfmt Svelte | `options-scripts-markup-styles`: ts-japi, tauri-plugin-ui-inspector. Off: others | on | Stricter: oxfmt then formats `.svelte` files |
| oxfmt on Markdown and TOML | Ignored: alyt, smapped-traces, tauri-plugin-ui-inspector, connectrpc-tauri (TOML). Formatted by `oxfmt --check .`: others | ignored | rumdl and tombi format these files in the 17 repositories with the organization's hk steps. Two formatters on one file disagree |
| oxfmt on `package.json` | Ignored: alyt, smapped-traces, ts-japi. Formatted: others | formatted when a script runs `oxfmt .` | Stricter. The hk step excludes `package.json`, because the sort-package-json step owns it. `sortPackageJson` is off, so oxfmt does not reorder keys |
| oxfmt on JSON and YAML in hk | `**/*.json`, `**/*.jsonc`, `**/*.yaml`, `**/*.yml`: alyt, smapped-traces, ts-japi. Not read: the 14 other repositories with the organization's hk steps | JSON formatted. YAML not formatted | Stricter for JSON. In a YAML flow mapping, oxfmt writes `{ bar: 0 }`, and the braces rule of ryl rejects it |
| rustfmt `imports_granularity`, `group_imports` | `Crate`, `StdExternalCrate`: connectrpc-tauri, if-changed, protovalidate-buffa. Default: others | not set | Stable rustfmt 1.100.0 ignores both options and prints a warning on each run |
| rustfmt `use_field_init_shorthand` | On: tauri-plugin-ui-inspector. Default (off): others | on | Stricter |
| rustfmt `edition` | `2024`: tauri-plugin-ui-inspector, toolconfig | local | A fact of each crate. `cargo fmt` gives rustfmt the edition of the crate |
| ruff `target-version` | `py312`: toolconfig | local | A fact of the project |
| cargo-deny `licenses.allow` | 5 lists of 6 to 14 licenses | Apache-2.0, MIT, Unicode-3.0, Zlib | Stricter: the licenses that every list allows. A repository allows another license for one crate with `[[licenses.exceptions]]` |
| cargo-deny `unused-allowed-license` | `allow`: addr-spec-rs, if-changed, protovalidate-buffa, unfmt. Default (`warn`): others | default | Stricter |
| cargo-deny `licenses.private.ignore` | `true`: connectrpc-tauri, sqlc-gen-sqlx, tauri-plugin-ui-inspector. Default (`false`): others | default | Stricter |
| cargo-deny `bans.multiple-versions` | `warn`: 6 repositories. `allow`: connectrpc-tauri, tauri-plugin-ui-inspector | default (`warn`) | Stricter of the values seen |
| cargo-deny `bans.allow-workspace` | `true`: protovalidate-buffa, sqlc-gen-sqlx | not set | Stricter |
| cargo-deny `bans.deny` | `chrono`, `chrono-tz`: protovalidate-buffa | local | A choice of that project. Three other repositories depend on `chrono` |
| shellcheck `external-sources` | `-x`: vscode-pdf. Default: others | on | Union: shellcheck also checks the files that a script sources |
| Shell indentation | Tabs (the shfmt default): sqlc-gen-sqlx, vscode-pdf. 2 spaces: scoped-git-token-action, toolconfig-action (`.editorconfig`) | 2 spaces | A style choice with two repositories on each side. Only toolconfig-action sets it, and spaces agree with the `*` section. 4 scripts change their indentation, not 6. shfmt reads it from `.editorconfig` |
| jactionlint profile | `correctness`: the 17 repositories with the organization's hk steps. `default`: toolconfig-action | `default` | Stricter: the `default` profile adds the security and policy rules. With no `profile` in the file, jactionlint prints a note on each run |
| zizmor minimum severity (hk) | `low`: the 17 repositories with the organization's hk steps. Every severity: toolconfig-action | every severity | Stricter |
| pinact rule for `dtolnay/rust-toolchain` | Ignored: addr-spec-rs, connectrpc-tauri, if-changed, protovalidate-buffa, sqlc-gen-sqlx, tauri-plugin-ui-inspector, unfmt. Default: the 10 other repositories with the organization's hk steps | ignored only for a commit pin | Stricter than the rule of the 7 repositories: pinact still rejects a branch or a tag. The action has no version tags, so its commit pins carry `# stable` |
| Python width | 100: toolconfig | 100 | The only repository with Python. Ruff's selected rules do not limit width |
| TOML width | tombi default: every repository | not set | Every repository. An explicit width makes tombi wrap arrays and inline tables |
| Changelogs and generated folders | Excluded by the 17 `hk.pkl` files of the organization's steps | Changelogs: rumdl and typos. Generated folders: oxfmt, oxlint, rumdl and typos | release-please writes most changelogs. The tools then agree with hk |
| harper ignored rules | 15 rules in the 17 repositories with the organization's hk steps. 1 to 6 more in 7 repositories | the 15 rules | Stricter: the fewest ignored rules |
| Clippy and Rust lint levels | protovalidate-buffa: `all`, `nursery`, `pedantic` `deny`. unfmt: `all`, `nursery`, `pedantic`, `restriction` `warn` with 19 `allow`. tauri-plugin-ui-inspector: `all`, `pedantic` and 4 Rust lints `warn`. toolconfig: `unreachable_pub`. Default: others | `all`, `nursery`, `pedantic` and the 4 Rust lints at `deny`. `restriction` off | Stricter for the groups. Clippy's documentation says not to turn on the whole `restriction` group. No repository turns on a `restriction` lint by name, so the 19 `allow` entries of unfmt have nothing to stop. unfmt allows `needless_borrowed_reference` only because of `pattern_type_mismatch`, a `restriction` lint. The table leaves it on |
| Clippy `redundant_pub_crate` and Rust `unreachable_pub` | toolconfig and tauri-plugin-ui-inspector turn on `unreachable_pub`. `nursery` holds `redundant_pub_crate` | `redundant_pub_crate` allowed | In a private module, `pub` breaks `unreachable_pub` and `pub(crate)` breaks `redundant_pub_crate`. Two repositories ask for `unreachable_pub` by name |

A setting with one value in every repository keeps that value.

## Change and verify

```sh
mise install
mise run check
```

The tests generate the profile in a fixture repository for Rust, TypeScript,
protobuf, shell, and a Dockerfile with a workflow. Each fixture imports the
profile as a consumer does. Then the tests run each tool on the fixture.
`hk check` runs the other tools on the files of this repository. A change to the
profile must keep every check green. A consumer moves to a new version when it
changes its `rev` and regenerates.

## License

[MIT](LICENSE).
