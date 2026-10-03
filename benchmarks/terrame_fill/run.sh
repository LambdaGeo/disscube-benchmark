#!/usr/bin/env bash
# ==============================================================================
# terrame_fill: DisSCube vs TerraME "Fill" on the same grid.
#   ./run.sh [all|run|compare] [dataset]      (default: all itaituba)
# ==============================================================================
set -euo pipefail

STAGE="${1:-all}"
DATASET="${2:-itaituba}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${WORKSPACE:-$HERE/data/$DATASET}"
REPORT="${REPORT:-$HERE/reports/$DATASET}"

stage_run() {
  echo "=== [1/2] DisSCube: fetch (SHA-256 verified) + derive on the TerraME grid ==="
  disscube validate "$HERE/$DATASET.toml"
  mkdir -p "$WORKSPACE"
  disscube run "$HERE/$DATASET.toml" --workspace "$WORKSPACE"
}

stage_compare() {
  echo "=== [2/2] Compare with the TerraME reference cells ==="
  python "$HERE/compare.py" "$HERE/$DATASET.compare.toml" --workspace "$WORKSPACE" --out "$REPORT"
}

case "$STAGE" in
  run)       stage_run ;;
  compare)   stage_compare ;;
  all)       stage_run; stage_compare ;;
  -h|--help|help)
    echo "Usage: ./run.sh [all|run|compare] [dataset]"
    echo "  run        fetch inputs and derive the variables with DisSCube"
    echo "  compare    compare the cube with the luccme-goldens fill reference (exit 1 on regression)"
    echo "  all        run + compare"
    ;;
  *) echo "Unknown stage '$STAGE' (try --help)"; exit 1 ;;
esac
