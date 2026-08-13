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
