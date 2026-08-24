#!/usr/bin/env bash
set -euo pipefail

repo_path="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
codex_home="${CODEX_HOME:-$HOME/.codex}"
projects_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
computer_name="${COMPUTER_NAME:-$(hostname)}"

backup_root="$repo_path/backups/$computer_name"
legacy_sync_root="$repo_path/要同步的Codex設定"
legacy_codex_root="$legacy_sync_root/.codex"

reset_dir() {
  rm -rf "$1"
  mkdir -p "$1"
}

copy_file_if_exists() {
  local source="$1"
  local dest="$2"
  if [ -f "$source" ]; then
    mkdir -p "$(dirname "$dest")"
    cp "$source" "$dest"
  fi
}

export_safe_config_toml() {
  local source="$1"
  local dest="$2"
  [ -f "$source" ] || return 0
  mkdir -p "$(dirname "$dest")"
  awk '
    /^\[/ {
      skip = 0
      if ($0 ~ /^\[projects\./) skip = 1
      if ($0 ~ /^\[marketplaces\./) skip = 1
      if ($0 ~ /^\[mcp_servers\./) skip = 1
      if ($0 ~ /^\[windows\]$/) skip = 1
    }
    skip { next }
    /^[[:space:]]*notify[[:space:]]*=/ { next }
    /C:\\|c:\\|C:\/|c:\/|\\\\\?\\|\\\\\.\\pipe\\|CODEX_HOME|TRUSTED_CODE_PATHS/ { next }
    { print }
  ' "$source" > "$dest"
}

mkdir -p "$backup_root/metadata"
mkdir -p "$legacy_sync_root" "$legacy_codex_root"
rm -rf "$backup_root/rules" "$legacy_codex_root/rules"
{
  echo "computer=$computer_name"
  echo "exported_at=$(date '+%Y-%m-%d %H:%M:%S %z')"
} > "$backup_root/metadata/export-info.txt"

copy_file_if_exists "$codex_home/AGENTS.md" "$backup_root/agents-root/AGENTS.md"
copy_file_if_exists "$codex_home/AGENTS.md" "$backup_root/agents-codex/AGENTS.md"
copy_file_if_exists "$codex_home/AGENTS.md" "$legacy_sync_root/AGENTS.md"
copy_file_if_exists "$codex_home/AGENTS.md" "$legacy_codex_root/AGENTS.md"
export_safe_config_toml "$codex_home/config.toml" "$backup_root/config/config.toml"
copy_file_if_exists "$backup_root/config/config.toml" "$legacy_codex_root/config.toml"

reset_dir "$backup_root/execution-profiles"
for profile_name in sol-auto.config.toml luna-manual.config.toml; do
  copy_file_if_exists "$codex_home/$profile_name" "$backup_root/execution-profiles/$profile_name"
  copy_file_if_exists "$codex_home/$profile_name" "$legacy_codex_root/$profile_name"
done

reset_dir "$backup_root/skills"
if [ -d "$codex_home/skills" ]; then
  find "$codex_home/skills" -mindepth 1 -maxdepth 1 ! -name '.system' -exec cp -R {} "$backup_root/skills/" \;
fi

reset_dir "$backup_root/workflows"
if [ -d "$projects_root" ]; then
  while IFS= read -r -d '' workflow_file; do
    project_name="$(basename "$(dirname "$(dirname "$workflow_file")")")"
    mkdir -p "$backup_root/workflows/$project_name"
    cp "$workflow_file" "$backup_root/workflows/$project_name/$(basename "$workflow_file")"
  done < <(find "$projects_root" -path "$repo_path" -prune -o -path '*/workflows/*' -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.md' \) -print0)
fi

reset_dir "$backup_root/sync-tools-and-docs"
cp -R "$repo_path/同步工具" "$backup_root/sync-tools-and-docs/同步工具"
find "$repo_path" -maxdepth 1 -type f \( -name '*.md' -o -name '*.txt' \) -exec cp {} "$backup_root/sync-tools-and-docs/" \;
for directory_name in schemas 文件; do
  if [ -d "$repo_path/$directory_name" ]; then
    cp -R "$repo_path/$directory_name" "$backup_root/sync-tools-and-docs/"
  fi
done
if [ -d "$repo_path/環境清單/current" ]; then
  mkdir -p "$backup_root/sync-tools-and-docs/環境清單"
  cp -R "$repo_path/環境清單/current" "$backup_root/sync-tools-and-docs/環境清單/"
fi

echo "Exported categorized Codex settings backup."
echo "Backup root: $backup_root"
echo "Categories: agents-root, agents-codex, config, execution-profiles, skills, workflows, sync-tools-and-docs, environment-manifest"
