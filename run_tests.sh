#!/bin/sh
set -ex

if [ -z ${VIRTUAL_ENV+x} ]; then
  pip install --user -q -r test-requirements.txt
else
  pip install -q -r test-requirements.txt
fi
PYTHONPATH=. py.test $@
pycodestyle
./tests/test_findpkg_integration.sh
