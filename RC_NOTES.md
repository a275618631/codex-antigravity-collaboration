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

- GitHub Pages uses a shared Jekyll layout for the technical reading pages.
- The original English Markdown files remain the canonical engineering documents.
- The HTML reading pages are localized Traditional Chinese presentation views derived from those documents; each page links back to its English source.
- The architecture homepage links to the rendered technical pages instead of raw `.md` files.
- No runtime capability or architecture scope changed.

## Traditional Chinese technical reading views

- The GitHub Pages technical reading pages are now localized in Traditional Chinese.
- The original English Markdown files remain the canonical engineering documents in the repository.
- Each localized page links back to its English source document.
- Product names and necessary technical terms remain in English where that is clearer, with Chinese explanations on first use.
