#!/usr/bin/env bash
#
# regenerate_artifacts.sh -- (re)render every figure and animation into
# infinity-lab/artifacts/, then rebuild the showcase gallery.
#
# Uses the repo venv (numpy + matplotlib + Pillow; ffmpeg on PATH) so the
# optional viz/animation layers run. It is idempotent: every run overwrites the
# same artifact filenames in place and echoes exactly what it wrote.
#
# Usage (from anywhere):
#     infinity-lab/scripts/regenerate_artifacts.sh
#
set -euo pipefail

# Resolve the repo root from this script's location (robust to CWD).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)"

ARTIFACTS_DIR="${REPO_ROOT}/artifacts"
VENV_PY="${REPO_ROOT}/.venv/bin/python"
PYTHONPATH_ROOTS="${REPO_ROOT}/packages/commons/src:${REPO_ROOT}/packages/gojo_infinity/src:${REPO_ROOT}/packages/mobius_rickness/src:${REPO_ROOT}/packages/central_finite_curve/src"

if [[ ! -x "${VENV_PY}" ]]; then
  echo "ERROR: venv interpreter not found at ${VENV_PY}" >&2
  echo "       create it with: python3 -m venv .venv && .venv/bin/python -m pip install numpy matplotlib Pillow pytest" >&2
  exit 1
fi

mkdir -p "${ARTIFACTS_DIR}"
export PYTHONPATH="${PYTHONPATH_ROOTS}"

echo "=== infinity-lab: regenerating artifacts into ${ARTIFACTS_DIR} ==="
echo "Interpreter: ${VENV_PY}"
if command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg: $(command -v ffmpeg) (MP4 export enabled)"
else
  echo "WARNING: ffmpeg not on PATH -- MP4 exports will fail." >&2
fi
echo

# ---------------------------------------------------------------------------
# 1) Static PNGs. Call the viz exporters directly so the written filenames
#    match the canonical artifact names exactly (the CLI --png uses different
#    per-lens filenames).
# ---------------------------------------------------------------------------
echo "--- [1/3] rendering PNGs (matplotlib, headless Agg) ---"
"${VENV_PY}" - "${ARTIFACTS_DIR}" <<'PY'
import sys, os
outdir = sys.argv[1]
from gojo_infinity.adapters.viz import (
    save_metric_blowup_png,
    save_series_convergence_png,
    save_covering_png,
    save_geodesic_bundle_png,
    save_length_divergence_png,
    save_geodesic_3d_png,
)
from mobius_rickness.adapters.viz import (
    save_strip_3d_png,
    save_krick_heatmap_png,
    save_ridge_png,
)

jobs = [
    (save_metric_blowup_png,    "gojo_metric_blowup.png"),
    (save_series_convergence_png, "gojo_series_convergence.png"),
    (save_covering_png,         "gojo_cover_convergence.png"),
    (save_geodesic_bundle_png,  "gojo_geodesic_bundle.png"),
    (save_length_divergence_png, "gojo_length_divergence.png"),
    (save_geodesic_3d_png,      "gojo_geodesic_3d.png"),
    (save_strip_3d_png,         "mobius_strip_curve.png"),
    (save_krick_heatmap_png,    "mobius_krick_heatmap.png"),
    (save_ridge_png,            "mobius_ridge.png"),
]
for fn, name in jobs:
    path = fn(os.path.join(outdir, name))
    print(f"  wrote {path}")
PY
echo

# ---------------------------------------------------------------------------
# 2) Gojo animations. The CLI 'animate OUTDIR' subcommand writes the two
#    baseline GIFs; --rotate adds the rotating 3-D GIF; --mp4 adds both MP4s.
#    These write the canonical artifact filenames directly.
# ---------------------------------------------------------------------------
echo "--- [2/3] rendering gojo_infinity animations (GIF + MP4) ---"
"${VENV_PY}" -m gojo_infinity.adapters.cli animate "${ARTIFACTS_DIR}" --rotate --mp4 \
  | sed 's/^/  /'
echo

# ---------------------------------------------------------------------------
# 3) Mobius animation. The CLI 'animate OUTDIR --mp4' writes the rotating GIF
#    and MP4 (mobius_rotating.gif / mobius_rotating.mp4) directly.
# ---------------------------------------------------------------------------
echo "--- [3/3] rendering mobius_rickness animation (GIF + MP4) ---"
"${VENV_PY}" -m mobius_rickness.adapters.cli animate "${ARTIFACTS_DIR}" --mp4 \
  | sed 's/^/  /'
echo

# ---------------------------------------------------------------------------
# 4) Central Finite Curve. The real viz exporter writes the projection PNG under
#    its canonical name, and the CLI 'animate OUTDIR' writes the walk GIF; --panels
#    adds the four-panel explainer, --rotate the rotating 3-D projection, and --mp4
#    the MP4 of each. All write the canonical artifact filenames directly:
#    central_finite_curve_four_panels.gif/.mp4 and
#    central_finite_curve_rotating_3d.gif/.mp4.
# ---------------------------------------------------------------------------
echo "--- [4/4] rendering central_finite_curve (PNG + walk/panels/rotating GIF/MP4) ---"
"${VENV_PY}" - "${ARTIFACTS_DIR}" <<'PY'
import sys, os
outdir = sys.argv[1]
from central_finite_curve.adapters.viz import save_projection_png

path = save_projection_png(
    os.path.join(outdir, "central_finite_curve_projection.png")
)
print(f"  wrote {path}")
PY
"${VENV_PY}" -m central_finite_curve.adapters.cli animate "${ARTIFACTS_DIR}" \
  --panels --rotate --mp4 \
  | sed 's/^/  /'
echo

# ---------------------------------------------------------------------------
# Rebuild the gallery (stdlib only -- use whatever python3 is available).
# ---------------------------------------------------------------------------
echo "--- building poster montage ---"
"${VENV_PY}" "${REPO_ROOT}/gallery/build_poster.py"
echo

echo "--- rebuilding gallery/index.html ---"
"${VENV_PY}" "${REPO_ROOT}/gallery/build_gallery.py"
echo

echo "=== done. Artifacts now in ${ARTIFACTS_DIR}: ==="
ls -1 "${ARTIFACTS_DIR}"
