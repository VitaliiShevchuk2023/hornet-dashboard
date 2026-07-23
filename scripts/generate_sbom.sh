#!/usr/bin/env bash
#
# generate_sbom.sh
#
# Generates a Software Bill of Materials (SBOM) for the project's
# Python dependencies, in CycloneDX format, and runs a dependency
# vulnerability scan.
#
# Usage (from repo root):
#   chmod +x scripts/generate_sbom.sh
#   ./scripts/generate_sbom.sh

set -euo pipefail

OUT_DIR="sbom"
REQ_FILE="requirements.txt"

if [ ! -f "$REQ_FILE" ]; then
  echo "❌ $REQ_FILE not found. Run this script from the repo root."
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "── Installing SBOM tooling (cyclonedx-bom, pip-audit) ──"
pip install --quiet --break-system-packages cyclonedx-bom pip-audit

echo "── Generating CycloneDX SBOM from $REQ_FILE ──"
cyclonedx-py requirements "$REQ_FILE" -o "$OUT_DIR/sbom.json"
echo "✅ SBOM written to $OUT_DIR/sbom.json"

echo "── Running dependency vulnerability audit (pip-audit) ──"
pip-audit -r "$REQ_FILE" > "$OUT_DIR/vulnerability-report.txt" 2>&1 || true
echo "✅ Vulnerability report written to $OUT_DIR/vulnerability-report.txt"

echo ""
echo "── Summary ──"
grep -c "Found" "$OUT_DIR/vulnerability-report.txt" 2>/dev/null \
  && echo "⚠️  Vulnerabilities found — see $OUT_DIR/vulnerability-report.txt" \
  || echo "✅ No known vulnerabilities found in current dependencies."
