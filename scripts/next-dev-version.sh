#!/usr/bin/env bash
# Compute the next patch version and append -dev.
# Example: 1.0.1 -> 1.0.2-dev
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <current_version>" >&2
  exit 1
fi

current="$1"
# Strip optional -dev suffix for arithmetic.
base="${current%-dev}"

IFS='.' read -r major minor patch <<< "$base"
if [[ -z "${major}" || -z "${minor}" || -z "${patch}" ]]; then
  echo "Invalid version format: ${current}" >&2
  exit 1
fi

next_patch=$((patch + 1))

printf "%s.%s.%s-dev\n" "$major" "$minor" "$next_patch"
