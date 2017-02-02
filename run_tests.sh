#!/bin/sh
set -ex

PYTHONPATH=. py.test $@
pep8 rdopkg
./tests/test_findpkg_integration.sh
