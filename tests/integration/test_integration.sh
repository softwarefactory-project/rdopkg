#!/bin/bash
# Run all integration tests for rdopkg.

set -e

env
if [ "${USER}" == "zuul-worker" ]; then
    export WORKSPACE=/home/zuul-worker
    echo "set workspace to $WORKSPACE"
fi

TESTS_PATH="`dirname \"$0\"`"
TESTS_PATH="`( cd \"$TESTS_PATH\" && pwd )`"

$TESTS_PATH/test_findpkg.sh
$TESTS_PATH/test_clone.sh
$TESTS_PATH/test_info.sh
