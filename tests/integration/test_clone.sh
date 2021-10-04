#!/bin/bash
# Integration tests for `rdopkg clone`

set -e

WORKSPACE="${WORKSPACE:-/tmp}"
TEST_PROJECT=python-stevedore

echo 'testing `rdopkg clone`'

pushd ${WORKSPACE}
rdopkg clone "$TEST_PROJECT"

TEST_DEP_PROJECT=python-eventlet
DEP_EXTRA_REPO=centos-distgit
rdopkg clone -e ${DEP_EXTRA_REPO} ${TEST_DEP_PROJECT}

pushd ${TEST_DEP_PROJECT}
git branch -a |grep ${DEP_EXTRA_REPO}
popd

echo 'rdopkg clone test OK'
rm -rf "$TEST_PROJECT"
rm -rf "$TEST_DEP_PROJECT"
popd
