#!/bin/bash
set -e
uv run pytest && echo "* Unit tests all pass *"
uv run mypy --ignore-missing-imports itercat test \
    && echo "* Full coherence to type annotations *"
uv run flake8 itercat test && echo "* Everything conforms to PEP8 *"
