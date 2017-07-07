#!/bin/sh
set -ex

pip install -q -r test-requirements.txt
PYTHONPATH=. py.test $@
pycodestyle
./tests/test_findpkg_integration.sh
