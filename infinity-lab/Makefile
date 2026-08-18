.DEFAULT_GOAL := help
VENV := .venv
PY := python3
VPY := $(VENV)/bin/python

.PHONY: help test test-full verify artifacts gallery poster venv clean

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

test:  ## Offline core tests (stdlib only; optional deps skip)
	$(PY) -m pytest -q

test-full:  ## Full suite via venv (numpy/matplotlib/ffmpeg run)
	$(VPY) -m pytest -q

verify:  ## Run both suites (scripts/verify.sh)
	bash scripts/verify.sh

artifacts:  ## Regenerate all figures/animations + gallery (venv)
	bash scripts/regenerate_artifacts.sh

gallery:  ## Rebuild gallery/index.html from artifacts/
	$(PY) gallery/build_gallery.py

venv:  ## Create venv and install optional deps (numpy/matplotlib/Pillow/pytest)
	$(PY) -m venv $(VENV)
	$(VPY) -m pip install -q numpy matplotlib Pillow pytest

poster:  ## Build the shareable montage poster (needs venv/matplotlib)
	$(VPY) gallery/build_poster.py

clean:  ## Remove __pycache__ / .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
