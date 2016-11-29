#!/bin/sh
set -x

PYTHONPATH=. py.test $@
pep8 rdopkg
./tests/test_findpkg_integration.sh
