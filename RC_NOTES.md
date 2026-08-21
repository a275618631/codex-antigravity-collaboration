# Release Candidate Notes

Date: 2026-08-21

This release candidate incorporates an adversarial review focused on scope discipline, architecture semantics, evidence, and privacy framing.

## Changes made

- Clarified that this repository is documentation-first and is not an installable runtime.
- Clarified that distributed write ownership is a coordination policy implemented with Git branch/worktree isolation, optimistic concurrency, and PR/review/merge gates — not a distributed lock service.
- Removed multi-host implication from the primary README topology; multi-host remains Exploratory.
- Clarified that reversible-pseudonym mappings remain ephemeral or local-vault state and are not synchronized as distributed coordination state.
- Added the MIT License.

## Scope unchanged

No new runtime, broker, database, gateway, scheduler, privacy product, or multi-host implementation was added.

The status model remains:

- Implemented
- Partial
- Planned
- Exploratory

## Documentation site

- GitHub Pages now renders the technical Markdown documents through a shared Jekyll layout and thin wrapper pages.
- Markdown remains the canonical source; the HTML reading views include and render that source at build time rather than duplicating document content.
- The architecture homepage links to the rendered technical pages instead of raw `.md` files.
- No runtime capability or architecture scope changed.
