#!/usr/bin/env bash
set -euo pipefail

repo_path="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
branch="${2:-}"
confirm_push="${3:-}"

cd "$repo_path"

"$(dirname "${BASH_SOURCE[0]}")/匯出目前設定到同步包.sh" "$repo_path"

if [ "$confirm_push" != "--confirm-push" ]; then
  echo "Codex settings exported locally. Commit/Push skipped; pass --confirm-push only after an explicit GitHub upload request."
  exit 0
fi

if ! git remote | grep -q '^origin$'; then
  echo "No GitHub remote configured. Add a private repo as origin first." >&2
  exit 1
fi

if [ -z "$branch" ]; then
  branch="$(git branch --show-current)"
fi

if [ -z "$branch" ]; then
  echo "Cannot detect current branch. Pass branch explicitly as the second argument." >&2
  exit 1
fi

if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
  echo "Refusing to commit or push directly to default branch '$branch'. Create a non-protected feature branch first." >&2
  exit 1
fi

git add backups 要同步的Codex設定 使用說明.md 同步規劃.md 同步工具

if ! git diff --cached --quiet; then
  git commit -m "Auto sync Codex settings $(date '+%Y-%m-%d %H:%M')"
else
  echo "No local Codex settings changes to commit."
fi

git push -u origin "$branch"

echo "Codex settings exported, committed if needed, and pushed to origin/$branch. Merge was not performed."
