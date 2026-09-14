# Repository guidance

This repository is the canonical shared source for cross-runtime rules and global core Skills.

- Start with `CANONICAL_MANIFEST.json` to resolve ownership and restore targets.
- Shared rules live in `shared/rules/`; global Skills live in `shared/skills/GLOBAL_CORE/`.
- Treat backups, generated copies, runtime caches, and open migration branches as evidence, not as canonical sources.
- Keep root `SKILL.md` files focused on routing, essential workflow, and safety boundaries. Read linked references only when the current task needs them.
- Preserve model-agnostic shared behavior. Put model- or platform-specific behavior in the owning thin-adapter repository.
- Make the smallest relevant change and use proportional validation. For Skill or manifest changes, run `pwsh -File scripts/validate-canonical-skills.ps1` and `git diff --check`.
- Do not weaken approval or secret-handling boundaries, merge default branches, or overwrite unrelated work.

