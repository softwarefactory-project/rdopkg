#!/bin/sh
set -x

PYTHONPATH=. py.test $@
pep8 rdopkg
