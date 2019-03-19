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


echo 'testing `rdopkg info -l LOCAL -i INFO_FILE`'

pushd ${WORKSPACE}
rm -rf rdoinfo
git clone "$RDOINFO_URL" rdoinfo
# move the info file to test -i/--info-file
mv rdoinfo/rdo-full.yml rdoinfo/custom-info.yml
rdopkg info -l ${WORKSPACE}/rdoinfo -i custom-info.yml \
    project:nova | grep 'name: openstack-nova'
rm -rf "${WORKSPACE}/rdoinfo"
popd
echo "...OK!"
