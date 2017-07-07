#!/bin/sh
set -ex

PYTHONPATH=. py.test $@
pycodestyle
./tests/test_findpkg_integration.sh
