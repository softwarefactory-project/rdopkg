#!/bin/bash
# Integration tests for `rdopkg clone`

set -e

WORKSPACE="${WORKSPACE:-/tmp}"
TEST_PROJECT=python-stevedore

echo 'testing `rdopkg clone`'

pushd ${WORKSPACE}
rdopkg clone "$TEST_PROJECT"

echo 'rdopkg clone test OK'
rm -rf "$TEST_PROJECT"
popd
