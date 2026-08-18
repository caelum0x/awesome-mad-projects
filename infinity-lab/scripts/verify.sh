#!/usr/bin/env bash
#
# verify.sh -- run BOTH test suites and report a one-line summary for each.
#
#   1) python3 -m pytest -q            offline core (stdlib only; optional
#                                       numpy/matplotlib tests SKIP).
#   2) .venv/bin/python -m pytest -q   full suite (numpy + matplotlib + ffmpeg
#                                       optional tests all RUN).
#
# Exits non-zero if EITHER suite fails. Safe to call from any directory: the
# repo root is resolved from this script's location and pytest is run there so
# the pyproject.toml pythonpath wiring resolves.
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)"
VENV_PY="${REPO_ROOT}/.venv/bin/python"

cd "${REPO_ROOT}"

# Run a pytest invocation, stream its output, and capture the final summary
# line. Args: <label> <python-executable>. Returns pytest's exit status.
run_suite() {
  local label="$1"; shift
  local py="$1"; shift
  local logfile
  logfile="$(mktemp)"
  echo "=== ${label}: ${py} -m pytest -q ==="
  "${py}" -m pytest -q 2>&1 | tee "${logfile}"
  local status="${PIPESTATUS[0]}"
  # The pytest summary is the last non-empty line of output.
  local summary
  summary="$(grep -E '.' "${logfile}" | tail -n 1)"
  rm -f "${logfile}"
  echo
  echo "SUMMARY [${label}]: ${summary} (exit ${status})"
  echo
  return "${status}"
}

overall=0

if [[ ! -x "$(command -v python3 || true)" ]]; then
  echo "ERROR: python3 not found on PATH" >&2
  overall=1
else
  run_suite "offline core (python3)" "python3" || overall=1
fi

if [[ ! -x "${VENV_PY}" ]]; then
  echo "ERROR: venv interpreter not found at ${VENV_PY}" >&2
  echo "       create it with: python3 -m venv .venv && .venv/bin/python -m pip install numpy matplotlib Pillow pytest" >&2
  overall=1
else
  run_suite "full suite (.venv)" "${VENV_PY}" || overall=1
fi

if [[ "${overall}" -eq 0 ]]; then
  echo "RESULT: both suites passed."
else
  echo "RESULT: at least one suite FAILED." >&2
fi
exit "${overall}"
