#!/usr/bin/env sh
set -eu

today="${1:-$(date +%F)}"
target_dir="ai_journal/sessions"
target_file="${target_dir}/${today}.md"

mkdir -p "${target_dir}"

if [ -f "${target_file}" ]; then
  echo "Log already exists: ${target_file}"
  exit 0
fi

sed "s/{{DATE}}/${today}/g" ai_journal/TEMPLATE.md > "${target_file}"
echo "Created: ${target_file}"

