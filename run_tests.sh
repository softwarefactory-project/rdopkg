#!/bin/sh
set -exuo pipefail

# avoid possible pytest errors due to precompiled files
export PYTHONDONTWRITEBYTECODE=1
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf || true

pip install -r test-requirements.txt -r requirements.txt -e .
PYTHONPATH=. py.test $@
pep8 rdopkg
./tests/test_findpkg_integration.sh
