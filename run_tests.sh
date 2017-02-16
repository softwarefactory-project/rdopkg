#!/bin/sh
set -ex

PYTHONPATH=. py.test $@
find . -name "*\.py" | xargs pep8 --ignore E501,E241
./tests/test_findpkg_integration.sh
