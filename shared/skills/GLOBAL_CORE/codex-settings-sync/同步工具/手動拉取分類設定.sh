#!/usr/bin/env bash
set -euo pipefail

repo_path="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
codex_home="${CODEX_HOME:-$HOME/.codex}"
target_workflows_path="$codex_home/workflows"
target_workflows_explicit=0
source_computer=""
categories=()
branch="master"
pull_remote=0
union_mode=0
list_sources=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) repo_path="$2"; shift 2 ;;
    --codex-home) codex_home="$2"; shift 2 ;;
    --target-workflows) target_workflows_path="$2"; target_workflows_explicit=1; shift 2 ;;
    --source) source_computer="$2"; shift 2 ;;
    --category) categories+=("$2"); shift 2 ;;
    --branch) branch="$2"; shift 2 ;;
    --pull) pull_remote=1; shift ;;
    --union) union_mode=1; shift ;;
    --list-sources) list_sources=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [ "$target_workflows_explicit" -eq 0 ]; then
  target_workflows_path="$codex_home/workflows"
fi

if [ "${#categories[@]}" -eq 0 ]; then
  categories=("all")
fi

cd "$repo_path"

if [ "$pull_remote" -eq 1 ]; then
  current_branch="$(git branch --show-current)"
  if [ -z "$current_branch" ]; then
    echo "Cannot detect the current Git branch. Switch to the target branch before --pull." >&2
    exit 1
  fi
  if [ "$current_branch" != "$branch" ]; then
    echo "Current branch is '$current_branch', but GitHub source branch is '$branch'. Switch to '$branch' before --pull." >&2
    exit 1
  fi
  if [ -n "$(git status --porcelain)" ]; then
    echo "Working tree is not clean. Commit or back up local sync-repo changes before --pull." >&2
    exit 1
  fi
  git pull --ff-only origin "$branch"
fi

backups_root="$repo_path/backups"
if [ "$list_sources" -eq 1 ]; then
  find "$backups_root" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;
  exit 0
fi

resolve_latest_source() {
  local latest=""
  local latest_stamp=""
  while IFS= read -r -d '' info_file; do
    source_name="$(basename "$(dirname "$(dirname "$info_file")")")"
    stamp="$(awk -F= '/^exported_at=/{print substr($0, index($0, "=")+1); exit}' "$info_file")"
    [ -n "$stamp" ] || stamp="0000-00-00 00:00:00"
    if [ -z "$latest" ] || [[ "$stamp" > "$latest_stamp" ]]; then
      latest="$source_name"
      latest_stamp="$stamp"
    fi
  done < <(find "$backups_root" -mindepth 3 -maxdepth 3 -type f -path '*/metadata/export-info.txt' -print0)

  if [ -z "$latest" ]; then
    echo "No source computer backup found under $backups_root." >&2
    exit 1
  fi
  printf '%s\n' "$latest"
}

if [ -z "$source_computer" ]; then
  source_computer="$(resolve_latest_source)"
  echo "Auto-selected latest source computer: $source_computer"
fi

source_root="$backups_root/$source_computer"
if [ ! -d "$source_root" ]; then
  echo "Backup source not found: $source_root" >&2
  exit 1
fi

copy_or_union_file() {
  local source="$1"
  local dest="$2"
  if [ ! -f "$source" ]; then
    echo "Skipped missing source: $source"
    return
  fi

  mkdir -p "$(dirname "$dest")"
  if [ "$union_mode" -eq 0 ] || [ ! -f "$dest" ]; then
    cp "$source" "$dest"
    return
  fi

  awk 'FNR==NR { seen[$0]=1; print; next } !seen[$0] { missing[++n]=$0; seen[$0]=1 } END { if (n > 0) { print ""; print "# --- union from remote backup ---"; for (i=1; i<=n; i++) print missing[i] } }' "$dest" "$source" > "$dest.tmp"
  mv "$dest.tmp" "$dest"
}

copy_or_union_dir() {
  local source_dir="$1"
  local dest_dir="$2"
  [ -d "$source_dir" ] || return 0
  while IFS= read -r -d '' source_file; do
    rel="${source_file#$source_dir/}"
    copy_or_union_file "$source_file" "$dest_dir/$rel"
  done < <(find "$source_dir" -type f -print0)
}

expanded=()
for category in "${categories[@]}"; do
  if [ "$category" = "all" ]; then
    expanded+=(agents-root agents-codex agents config execution-profiles skills workflows workflow-definitions sync-tools-and-docs)
  else
    expanded+=("$category")
  fi
done

for category in "${expanded[@]}"; do
  case "$category" in
    agents-root) copy_or_union_file "$source_root/agents-root/AGENTS.md" "$codex_home/AGENTS.md" ;;
    agents-codex) copy_or_union_file "$source_root/agents-codex/AGENTS.md" "$codex_home/AGENTS.md" ;;
    agents) copy_or_union_dir "$source_root/agents" "$codex_home/agents" ;;
    config) copy_or_union_file "$source_root/config/config.toml" "$codex_home/config.toml" ;;
    execution-profiles)
      for profile_name in sol-auto.config.toml luna-manual.config.toml; do
        profile_source="$source_root/execution-profiles/$profile_name"
        if [ ! -f "$profile_source" ]; then
          echo "Required execution profile missing: $profile_source" >&2
          exit 1
        fi
        copy_or_union_file "$profile_source" "$codex_home/$profile_name"
      done
      ;;
    skills) copy_or_union_dir "$source_root/skills" "$codex_home/skills" ;;
    workflows) copy_or_union_dir "$source_root/workflows" "$target_workflows_path" ;;
    workflow-definitions) copy_or_union_dir "$source_root/workflow-definitions" "$target_workflows_path" ;;
    sync-tools-and-docs) copy_or_union_dir "$source_root/sync-tools-and-docs" "$repo_path" ;;
    *) echo "Invalid category: $category" >&2; exit 1 ;;
  esac
done

echo "Applied selected categories from $source_computer."
echo "Categories: ${expanded[*]}"
echo "Union mode: $union_mode"
