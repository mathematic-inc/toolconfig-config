# ToolConfig policy for mathematic-inc

The shared [ToolConfig](https://github.com/mathematic-inc/toolconfig) policy for
the repositories of mathematic-inc. It needs ToolConfig 2026.11.4 or newer and
Git.

The policy is one profile, `profiles/org/.toolconfig.pkl`. It holds every lint,
format and check tool that a mathematic-inc repository uses. Where two
repositories used different settings, the profile keeps the stricter one.
[Decisions](#decisions) gives each choice and its reason.

## Import

Amend ToolConfig's schema in the repository's `.toolconfig.pkl` and extend the
profile:

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

- paths, such as the `modules` of `buf.yaml`;
- exclusions of generated, vendored and built folders;
- word lists for typos;
- exceptions, each with a comment that gives its reason.

Local tables merge with the profile key by key. A local list replaces the list
of the profile. Thus, a local `ignorePatterns` or `extend-exclude` list must
repeat the entries of the profile that it keeps.

Delete each native file that the profile writes before the first
`toolconfig generate`. ToolConfig does not overwrite a file that it did not
write. Then run `toolconfig init --gitignore`, so that Git ignores the
generated files. Commit `.toolconfig.pkl`, `.toolconfig.lock`, `.editorconfig`
and `.gitignore`.

Run `toolconfig generate` before the checks: in the hk hooks and in CI. Run
`toolconfig check --strict` in CI.

## What the profile writes

| Tool | File | Settings |
| --- | --- | --- |
| EditorConfig | `.editorconfig` | UTF-8, LF, final newline, no trailing whitespace, 2 spaces, width 100; Rust and Python 4 spaces; Go and Make tabs; Markdown width 80 |
| actionlint (read by jactionlint) | `.github/actionlint.yaml` | profile `default` |
| buf | `buf.yaml` | `lint` uses `STANDARD`, `breaking` uses `FILE` |
| cargo-deny | `deny.toml` | licenses Apache-2.0, MIT, Unicode-3.0, Zlib; wildcards and unknown sources denied; duplicate versions warn |
| gitleaks | `.gitleaks.toml` | the default rules |
| hadolint | `.hadolint.yaml` | the default rules |
| knip | `knip.json` | configuration hints are errors |
| lychee | `lychee.toml` | offline, no progress bar |
| oxfmt | `.oxfmtrc.json` | semicolons, double quotes, sorted imports, Svelte files; no Markdown or TOML |
| oxlint | `.oxlintrc.json` | `correctness`, `suspicious`, `pedantic` and `perf` denied; type-aware rules; warnings fail |
| pinact | `.pinact.yaml` | accepts `# stable` on `dtolnay/rust-toolchain` |
| ruff | `ruff.toml` | width 100, 4 spaces |
| rumdl | `.rumdl.toml` | every rule, line length 80; changelogs excluded |
| rustfmt | `rustfmt.toml` | width 100, 4 spaces, field init shorthand |
| ryl | `.ryl.toml` | the YAML rules of every repository |
| shellcheck | `.shellcheckrc` | follows sourced files |
| tombi | `tombi.toml` | 2 spaces, LF |
| ty | `ty.toml` | the default rules |
| typos | `typos.toml` | changelogs and generated folders excluded |

The profile excludes these generated folders from oxfmt, oxlint, rumdl and
typos: `dist`, `gen`, `generated`, `node_modules`, `target` and `vendor`.

Type-aware oxlint rules need `oxlint-tsgolint`. oxfmt formats a Svelte file
only when `svelte` is in the `node_modules` folder of that oxfmt.

## Outside ToolConfig

These settings are not in a file that ToolConfig writes.

The hk steps carry the settings of harper, zizmor, ghalint, kingfisher,
shellharden and sort-package-json as command-line options. `hk.pkl` in this
repository has the steps of the organization. The harper step ignores only the
rules that every repository ignores. The zizmor step reports findings of every
severity. The jactionlint step takes its profile from `.github/actionlint.yaml`,
so it has no `--profile` option.

Clippy reads its lint levels from `Cargo.toml`, which ToolConfig does not write.
Each Rust repository puts this table in its `Cargo.toml`. A single crate uses
`[lints]`.

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
| Markdown line length (rumdl MD013) | off: claude-tools-mcp, connectrpc-tauri, if-changed, mcpr, smapped-traces, sqlc-gen-sqlx, tauri-plugin-ui-inspector, ts-japi, unfmt, vscode-api-linter, vscode-latex, vscode-pdf; on at 80: addr-spec-rs, alyt, connectrpc-sdk, noop, protovalidate-buffa | on at 80 | Stricter: a rule on and the lower limit |
| rumdl MD024, MD033, MD036, MD057 | off: vscode-api-linter (MD024, MD033), ts-japi (MD033), alyt `docs/plans` (MD036), smapped-traces and sqlc-gen-sqlx (MD057); on: others | on | Stricter |
| Trailing whitespace in Markdown | kept: toolconfig; removed: the 17 repositories with hk | removed | Stricter |
| oxlint categories | `correctness`, `suspicious`, `pedantic` and `perf` `deny`: 9 repositories; `correctness` `error`: bucket-cache-action | all four `deny` | Stricter |
| oxlint type-aware rules | on: bucket-cache-action, ts-japi (`no-deprecated` only); off: 8 repositories | on | Stricter |
| oxlint unused disable directives | `deny`: 9 repositories; default: bucket-cache-action | `deny` | Stricter |
| oxlint `require-unicode-regexp` flag | `v`: 7 repositories and tauri-plugin-ui-inspector apps; `u`: alyt, tauri-plugin-ui-inspector `packages` | `v` | Stricter: the `v` flag rejects more patterns; most repositories use it |
| oxlint `unicorn/require-post-message-target-origin`, `unicorn/prefer-dom-node-dataset` | `allow`: vscode-pdf, tauri-plugin-ui-inspector; `deny` through the suspicious and pedantic categories: others | `deny` | Stricter. An exception stays local, with its reason |
| oxfmt `sortImports` | on: 9 repositories; default (off): bucket-cache-action | on | Stricter |
| oxfmt `sortPackageJson` | off: 9 repositories; default (on): bucket-cache-action | off | sort-package-json sorts `package.json` in the hk repositories, and the two orders differ; most repositories use it |
| oxfmt Svelte | `options-scripts-markup-styles`: ts-japi, tauri-plugin-ui-inspector; off: others | on | Stricter: oxfmt then formats `.svelte` files |
| oxfmt on Markdown and TOML | ignored: alyt, tauri-plugin-ui-inspector, connectrpc-tauri (TOML); formatted by `oxfmt --check .`: others | ignored | rumdl and tombi format these files in every repository with hk, and the `hk.pkl` files say so. Two formatters on one file disagree |
| oxfmt on `package.json` | ignored: alyt, smapped-traces, ts-japi; formatted: others | formatted | Stricter. `sortPackageJson` is off, so oxfmt does not reorder keys |
| rustfmt `imports_granularity`, `group_imports` | `Crate`, `StdExternalCrate`: connectrpc-tauri, if-changed, protovalidate-buffa; default: others | not set | Stable rustfmt 1.99.1 ignores both options and prints a warning on each run |
| rustfmt `use_field_init_shorthand` | on: tauri-plugin-ui-inspector; default (off): others | on | Stricter |
| rustfmt `edition` | `2024`: tauri-plugin-ui-inspector | local | A fact of each crate. `cargo fmt` gives rustfmt the edition of the crate |
| cargo-deny `licenses.allow` | 4 lists of 6 to 14 licenses | Apache-2.0, MIT, Unicode-3.0, Zlib | Stricter: the licenses that every list allows. A repository allows another license for one crate with `[[licenses.exceptions]]` |
| cargo-deny `unused-allowed-license` | `allow`: addr-spec-rs, if-changed, protovalidate-buffa, unfmt; default (`warn`): others | default | Stricter |
| cargo-deny `licenses.private.ignore` | `true`: connectrpc-tauri, sqlc-gen-sqlx, tauri-plugin-ui-inspector; default (`false`): others | default | Stricter |
| cargo-deny `bans.multiple-versions` | `warn`: 6 repositories; `allow`: connectrpc-tauri, tauri-plugin-ui-inspector | `warn` | Stricter of the values seen |
| cargo-deny `bans.allow-workspace` | `true`: protovalidate-buffa, sqlc-gen-sqlx | not set | Stricter |
| cargo-deny `bans.deny` | `chrono`, `chrono-tz`: protovalidate-buffa | local | A choice of that project. Three other repositories depend on `chrono` |
| shellcheck `external-sources` | `-x`: vscode-pdf; default: others | on | Union: shellcheck also checks the files that a script sources |
| Shell indentation | tabs (the shfmt default): sqlc-gen-sqlx, vscode-pdf; 2 spaces: scoped-git-token-action, toolconfig-action (`.editorconfig`) | 2 spaces | A style choice with two repositories on each side. Only toolconfig-action sets it, spaces agree with the `*` section, and 4 scripts change, not 6. shfmt reads it from `.editorconfig` |
| jactionlint profile | `correctness`: the 17 repositories with the organization's hk steps; `default`: toolconfig-action | `default` | Stricter: the `default` profile adds the security and policy rules |
| zizmor minimum severity (hk) | `low`: the 17 repositories with the organization's hk steps; every severity: toolconfig-action | every severity | Stricter |
| Python width | 100: toolconfig | 100 | The only repository with Python. Ruff's selected rules do not limit width |
| TOML width | tombi default: every repository | not set | Most repositories. An explicit width makes tombi wrap arrays and inline tables |
| Changelogs and generated folders | excluded by every `hk.pkl` | excluded in rumdl and typos | release-please writes the changelogs. The tools then agree with hk |
| harper ignored rules | 15 rules in every repository; 1 to 6 more in 6 repositories | the 15 rules | Stricter: the fewest ignored rules |
| Clippy and Rust lint levels | protovalidate-buffa: `all`, `nursery`, `pedantic` `deny`; unfmt: `all`, `nursery`, `pedantic`, `restriction` `warn` with 19 `allow`; tauri-plugin-ui-inspector: `all`, `pedantic` and 4 Rust lints `warn`; toolconfig: `unreachable_pub`; default: others | `all`, `nursery`, `pedantic` and the 4 Rust lints at `deny`; `restriction` off | Stricter for the groups. Clippy's documentation says not to turn on the whole `restriction` group, and no repository turns on a `restriction` lint by name. Thus, the 19 `allow` entries of unfmt have no lint to stop. The one exception is `needless_borrowed_reference`; it is on, because the `restriction` lint that it conflicted with is off |
| Clippy `redundant_pub_crate` and Rust `unreachable_pub` | toolconfig and tauri-plugin-ui-inspector turn on `unreachable_pub`; `nursery` holds `redundant_pub_crate` | `redundant_pub_crate` allowed | In a private module, `pub` breaks `unreachable_pub` and `pub(crate)` breaks `redundant_pub_crate`. Two repositories ask for `unreachable_pub` by name |

Some settings had one value in every repository that set them. The profile keeps
that value. These settings are:

- buf `STANDARD` and `FILE`;
- cargo-deny wildcards and unknown sources `deny`;
- the default rules of gitleaks;
- knip configuration hints as errors;
- lychee offline;
- the oxlint rules of the shared `.oxlintrc.json`;
- oxfmt semicolons and double quotes;
- the pinact rule for `dtolnay/rust-toolchain`;
- the ryl rules;
- zizmor hash pins for every action. toolconfig-action writes this in
  `.github/zizmor.yml`, and it is the default of zizmor 1.32, so the profile
  writes no file.

ToolConfig 2026.11.4 writes ryl's projected options in the top-level `rules`
table. ryl 0.29 ignores that table when `lint.rules` is set, and prints a
warning. Until ToolConfig writes `lint.rules`, the profile writes `.ryl.toml` as
a `files` output.

## Change and verify

```sh
mise install
mise run check
```

The tests generate the profile in a fixture repository for each language family:
Rust, TypeScript, Python, protobuf, shell, and documents with workflows. Then
they run each tool on the fixture. A change to the profile must keep every test
green. A consumer moves to a new version when it changes its `rev` and
regenerates.

## License

[MIT](LICENSE).
