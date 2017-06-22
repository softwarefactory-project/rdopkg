#!/bin/sh
set -exuo pipefail

# avoid possible pytest errors due to precompiled files
export PYTHONDONTWRITEBYTECODE=1
find . | grep -E "(__pycache__|\.pyc|\.pyo)$" | xargs rm -rf || true

PYTHONPATH=. py.test $@
PYTHONPATH=. behave --format=progress
python -m pycodestyle
./tests/test_findpkg_integration.sh
