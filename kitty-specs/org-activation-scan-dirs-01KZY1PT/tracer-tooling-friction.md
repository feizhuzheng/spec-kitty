# Tracer: Tooling Friction

## Specify phase (2026-08-13)

`spec-kitty specify org-activation-scan-dirs --mission-type software-dev --topology
single_branch --json` ran cleanly, non-interactively, and produced no prompt — no friction
there. One naming surprise worth recording: the CLI did not scaffold the mission at the
requested slug `org-activation-scan-dirs`; it minted `org-activation-scan-dirs-01KZY1PT`
(appending an 8-char mission-id disambiguator) and used that as `mission_slug`, `slug`, and the
`kitty-specs/` directory name. This is normal `spec-kitty specify` behavior (every recent
mission directory in this repo carries the same `-<8char>` suffix), not a defect — but a
dispatcher instruction that says "seed tracer files under
`kitty-specs/org-activation-scan-dirs/`" needs the operator or the calling skill to resolve the
actual directory from the command's own JSON output (`feature_dir` / `mission_slug`) rather than
assuming the bare slug is the final path. Recorded here so a successor does not re-derive it.

The `spec.md` scaffold itself was written empty (0 bytes) — no template skeleton to fill in for
`mission-type software-dev`, unlike `research`/`documentation` mission types which ship a
`templates/spec-template.md`. The `next_step` field ("Open spec_file and replace the scaffold
with a complete specification") was accurate: there was no scaffold text to replace, only an
empty file to author from scratch. Cross-checked the structure against several existing
`kitty-specs/*/spec.md` files of comparable (surgical, single-defect) scope to match repo
convention rather than inventing a new shape.

## Commit blocked (2026-08-13, phase-agent follow-up)

Two compounding blockers prevented `spec-kitty safe-commit` from landing this spec at all,
both recorded as new entries in the workspace-root `SPEC-KITTY-LEDGER.md` (SK-11; SK-09
already covered the first half from a sibling mission):

1. **Topology choice mattered more than expected.** `--topology single_branch` was chosen
   over the CLI's own default (`coord`) as proportionate to a ~5 LOC surgical fix. Every
   other mission in this repo's `kitty-specs/` uses `coord`, which mints a dedicated
   non-protected branch (`feat/...`, `design/...`) at specify time. `single_branch` is a
   "branch-flat" shape per the CLI's own `--help` text — it mints no branch and sets
   `meta.json`'s `target_branch` to the literal base branch, which on this repo is the
   protected `main`. `safe_commit` then refuses outright. In hindsight, `coord` (or any
   coordination-bearing topology) should have been used regardless of mission size, purely
   to get a non-protected landing branch — this is now the corroborating half of ledger
   entry SK-09 (already verified once on the sibling `org-pack-drg-root-graph-guard`
   mission with `--topology lanes`, same failure shape).
2. **No git identity in this checkout, and `safe_commit` doesn't say so.** After creating a
   PR branch per the charter's own sanctioned remedy for (1) — a deviation from this
   mission's branch-discipline instruction, done once, for diagnosis, and not repeated —
   the commit still failed, with `safe_commit` reporting only "git commit failed" and no
   further detail. The real cause, confirmed by checking `git config user.name`/`user.email`
   (local and `--global`) directly: both empty, no `[user]` section anywhere. No commit can
   succeed in this container until an operator configures a git identity — something this
   mission is not authorized to do itself (git-config mutation is out of scope for a phase
   agent). Filed as ledger entry SK-11.

**Net effect**: spec.md, meta.json, and the three tracer files exist on disk, fully authored,
but are **uncommitted** as of this entry. The mission is BLOCKED pending operator action
(configure a git identity for this checkout; optionally also confirm the desired topology
for redo, since `single_branch` cannot be changed post-scaffold and the existing mission
directory should not be scaffolded a second time per RESUME discipline).

## Resolution (2026-08-13, same day, operator unblocked both)

Operator configured a global git identity (`MOES-Media` /
`34285209+MOES-Media@users.noreply.github.com` — confirmed via `git config user.email` before
retrying) and ratified the `pr/org-activation-scan-dirs` branch (created earlier during
diagnosis, same SHA as `main`, no divergence) as the working branch for this mission, per the
charter's own Agent Push Authorization remedy for protected-branch refusals — the same
adjudication already made for the sibling `org-pack-drg-root-graph-guard` mission. The
`single_branch` topology scaffold was kept as-is (no re-scaffold).

With HEAD on `pr/org-activation-scan-dirs` (not `main`) and identity configured,
`spec-kitty safe-commit kitty-specs/org-activation-scan-dirs-01KZY1PT --to-branch
pr/org-activation-scan-dirs --message "..." --json` **succeeded on the first try** —
no fallback to plain `git commit` was needed. Commit `8902a7453`. This confirms both
blockers (SK-09's protected-branch-on-`main` refusal, SK-11's missing identity) were the
full and only cause; once off `main` and with identity present, `safe_commit` behaves
exactly as documented.

## Plan phase (2026-08-13)

`spec-kitty plan --mission org-activation-scan-dirs-01KZY1PT --json` ran cleanly on the first
call, non-interactively, no prompt, no hang. It scaffolded `plan.md` from the software-dev
command template's own skeleton (Summary / Technical Context / Charter Check / Project
Structure / Complexity Tracking / Implementation Concern Map) — unlike `spec.md` at the specify
phase, this scaffold was **not** empty; it carries real section headers and placeholder text, so
there was no need to fall back to hand-authoring from a separate `plan-template.md` (no such
file exists for the `software-dev` mission type — confirmed by a direct search of
`src/doctrine/missions/` — the software-dev command template referenced in the scaffold's own
`Note` line, `.kittify/overrides/missions/software-dev/command-templates/plan.md`, is the
canonical source, not a distinct fill-in template). The command's JSON response reported
`"result": "blocked"` with `blocked_reason` citing "Technical Context ... Language/Version is
missing or carries only placeholder content" — this is the expected first-pass gate telling the
caller to replace placeholder text before the mission can advance past planning, not a tooling
defect. No workaround was needed: filling in the Technical Context section (and the rest of the
scaffold) with concrete content, per this document's own instructions, satisfies that gate on
the next `spec-kitty next`/status check. No new ledger entry was warranted — this is normal,
documented `spec-kitty plan` behavior, not a repeat of SK-09/SK-11's branch/identity class of
blocker (this checkout already had both resolved at the specify phase).

## Tasks phase (2026-08-13)

Mechanics: `spec-kitty agent context resolve --action tasks_outline --mission
org-activation-scan-dirs-01KZY1PT --json` and the returned `check_prerequisites` command both
ran cleanly, non-interactively, first try, and confirmed `feature_dir` as expected. Worth
recording for a successor: `tasks-outline` and `tasks-packages` are **not** literal `spec-kitty`
CLI subcommands — they are the prompt/mission-step template names
(`.kittify/overrides/missions/software-dev/command-templates/tasks-outline.md`,
`tasks-packages.md`) that this phase-agent follows by hand. The actual CLI surface backing this
phase is `spec-kitty agent context resolve`, `spec-kitty agent mission check-prerequisites`,
`spec-kitty agent mission finalize-tasks`, and `spec-kitty agent tasks map-requirements` — there
is no `spec-kitty tasks-outline` or `spec-kitty tasks-packages` command to invoke; `wps.yaml` and
`tasks/WP01-*.md` were authored directly by hand per the templates' documented schema, then
handed to `finalize-tasks` for parsing/validation/commit. This is expected, documented shape
(the templates are prompt scaffolding, not CLI entry points), not a defect.

**Real defect found — `finalize-tasks` requirement-mapping parser scans whole-document prose,
not just the Requirements table, for `FR-NNN`-shaped substrings.** With `wps.yaml` and
`tasks/WP01-org-scan-dirs-flat-layout-fix.md` written (one WP, `requirement_refs: [FR-001,
FR-002, FR-003]`, matching spec.md's Requirements table exactly), `spec-kitty agent mission
finalize-tasks --mission org-activation-scan-dirs-01KZY1PT --json` failed:

```json
{"error": "Requirement mapping validation failed", "missing_requirement_refs_wps": [],
"unknown_requirement_refs": {}, "unmapped_functional_requirements": ["FR-021"],
"dependencies_parsed": {"WP01": []},
"requirement_refs_parsed": {"WP01": ["FR-001", "FR-002", "FR-003"]}}
```

Root cause, traced to `src/specify_cli/requirement_mapping.py:104-117`
(`parse_requirement_ids_from_spec_md`) via its caller
`src/specify_cli/cli/commands/agent/mission_finalize.py:342-353`
(`_read_spec_requirement_ids`) and `:609-663` (`_validate_requirement_mapping`): the parser runs
`_REF_FIND_PATTERN` (`\b(?:FR|NFR|C)-\d+\b`) over spec.md's **entire raw text**, not scoped to
the Requirements table rows, and classifies every match starting with `FR-` as a "functional
requirement this spec defines" that some WP must cover. `spec.md:124` cites, in explanatory
prose about the failure mechanism (not in the Requirements table), an **unrelated, pre-existing,
already-implemented mechanism** in a different part of the codebase: "`CharterPackManager.activate`'s
FR-021 default-pack materialization (`src/charter/pack_manager.py:601-616` ...)". That citation's
`FR-021` — a foreign requirement ID from different, already-shipped code, not one of *this*
spec's three Requirements-table rows (FR-001/002/003) — gets swept into `functional_spec_requirement_ids`
by the whole-document scan and then reported as "unmapped" because, correctly, no WP in this
mission claims it (WP01 does not implement or touch `pack_manager.py`'s FR-021 mechanism at all).

No CLI escape hatch exists: `spec-kitty agent tasks map-requirements --help` offers `--wp`,
`--refs`, `--batch`, `--replace`, `--tracker-ref` — no flag to mark a spec.md-cited ID as
"external/citation-only" or to scope parsing to the Requirements table. Mapping `FR-021` to WP01
via `map-requirements` was considered and rejected as dishonest (WP01 genuinely does not
implement FR-021's behavior, and doing so would misrepresent coverage). Hand-editing spec.md to
remove or reword the citation was also rejected — spec.md is this mission's already-reviewed,
PASSED, binding contract; a phase-agent authoring tasks has no mandate to edit it to route around
a downstream tool's false positive. Per this mission's own governing instructions, the correct
response to a `finalize-tasks` refusal like this is to capture the exact output and report it as
BLOCKED-worthy tooling friction rather than hand-patch `tasks.md`/WP frontmatter/`meta.json` — so
this entry is that capture. **Suggested upstream fix** (not implemented here, out of this
mission's scope — C-001 bounds this mission to `_org_scan_dirs` and its own tests, not
`requirement_mapping.py`): scope `parse_requirement_ids_from_spec_md`'s functional-ID extraction
to the `### Functional Requirements` markdown table's `| FR-NNN |` rows specifically, rather than
`findall`-ing the entire document body, so a spec.md that legitimately cites another mission's
historical requirement ID as mechanism evidence does not get misread as defining that ID itself.

**Net effect**: `wps.yaml` and `tasks/WP01-org-scan-dirs-flat-layout-fix.md` exist on disk,
fully authored, matching the plan's single-WP shape exactly, but `finalize-tasks` has not
committed them — no `tasks.md` has been generated, and no commit landed on `pr/org-activation-scan-dirs`
for the tasks phase as of this entry. The mission is BLOCKED pending an operator decision on how
to handle the false-positive `FR-021` match (accept a documented exception, file the parser fix
as a tracked upstream issue and wait, or explicitly authorize a scoped edit this phase-agent was
not authorized to make unilaterally).
