#!/bin/bash
set -e
python runtests.py && echo "* Unit tests all pass *"
mypy --ignore-missing-imports itercat test/_test.py runtests.py \
    && echo "* Full coherence to type annotations *"
flake8 itercat test && echo "* Everything conforms to PEP8 *"
