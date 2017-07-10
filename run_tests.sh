#!/bin/sh
set -ex

pip install -r test-requirements.txt
python -m pep8 rdopkg
PYTHONPATH=. py.test $@
./tests/test_findpkg_integration.sh
