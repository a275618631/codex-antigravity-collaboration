#!/bin/sh
set -eu
python3 -m github_handoff --config "${1:-$HOME/.config/github-handoff/config.json}" doctor
echo "Verified only. No LaunchAgent or background service was installed."
