#!/bin/bash
# Integration tests for `rdopkg info`

set -e

WORKSPACE="${WORKSPACE:-/tmp}"
RDOINFO_URL="https://github.com/redhat-openstack/rdoinfo"


echo 'testing `rdopkg info`'

pushd ${WORKSPACE}
rdopkg info project:nova | grep 'name: openstack-nova'
popd
echo "...OK!"


echo 'testing `rdopkg info -l LOCAL`'

pushd ${WORKSPACE}
rm -rf rdoinfo
git clone "$RDOINFO_URL" rdoinfo
rdopkg info -l ${WORKSPACE}/rdoinfo project:nova \
    | grep 'name: openstack-nova'
rm -rf "${WORKSPACE}/rdoinfo"
popd
echo "...OK!"
