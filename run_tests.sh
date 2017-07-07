#!/bin/sh
set -ex

if [ -z ${VIRTUAL_ENV+x} ]; then
  pip install --user -r test-requirements.txt
else
  pip install -r test-requirements.txt
fi
PYTHONPATH=. py.test $@
python -m pycodestyle
./tests/test_findpkg_integration.sh
