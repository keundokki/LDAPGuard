#!/usr/bin/env bash
# Update version across VERSION, pyproject.toml, Helm values, and Chart.yaml.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <new_version>" >&2
  exit 1
fi

new_version="$1"

# Update VERSION file (single source of truth for CI/CD).
echo "${new_version}" > VERSION

# Update pyproject.toml version. If no version field exists, add one under [project].
if grep -qE '^\[project\]' pyproject.toml; then
  if grep -qE '^version\s*=' pyproject.toml; then
    sed -i.bak -E "s/^version\s*=\s*\".*\"/version = \"${new_version}\"/" pyproject.toml
  else
    # Insert version after [project] header.
    awk -v ver="${new_version}" '
      $0 ~ /^\[project\]$/ {print; print "version = \"" ver "\""; next} {print}
    ' pyproject.toml > pyproject.toml.tmp
    mv pyproject.toml.tmp pyproject.toml
  fi
else
  echo "[project]" >> pyproject.toml
  echo "version = \"${new_version}\"" >> pyproject.toml
fi

rm -f pyproject.toml.bak

# Update Helm chart versions.
sed -i.bak -E "s/^version:\s*.*/version: ${new_version}/" helm/Chart.yaml
sed -i.bak -E "s/^appVersion:\s*.*/appVersion: \"${new_version}\"/" helm/Chart.yaml

# Update Helm image tags for LDAPGuard services only (api/web/worker).
awk -v ver="${new_version}" '
  BEGIN {section=""; sub=""}
  /^[^[:space:]]/ {section=""; sub=""}
  /^images:/ {section="images"; print; next}
  section=="images" && /^  api:/ {sub="api"; print; next}
  section=="images" && /^  web:/ {sub="web"; print; next}
  section=="images" && /^  worker:/ {sub="worker"; print; next}
  section=="images" && /^  [a-zA-Z0-9_-]+:/ {sub=""; print; next}
  section=="images" && sub!="" && /^    tag:/ {print "    tag: \"" ver "\""; next}
  {print}
' helm/values.yaml > helm/values.yaml.tmp
mv helm/values.yaml.tmp helm/values.yaml

# Update values.yaml appVersion metadata.
sed -i.bak -E "s/^  appVersion:\s*\".*\"/  appVersion: \"${new_version}\"/" helm/values.yaml

rm -f helm/Chart.yaml.bak helm/values.yaml.bak

printf "Updated versions to %s\n" "${new_version}"
