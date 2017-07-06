#!/bin/bash
# Integration tests for findpkg

set -e

GIT_BASE_URL="https://review.rdoproject.org/r/p"
WORKSPACE="${WORKSPACE:-/tmp}"

function test_rdopkg_findpkg(){
    PKG_NAME=$(rdopkg findpkg $1 -l ${WORKSPACE}/rdoinfo | awk '/^name/ {print $2}')
    if [ $2 != $PKG_NAME ]; then
        echo "$0 FAILED EXPECTED: $@ (GOT: $PKG_NAME)"
        return 1
    fi
    echo -n .
    return 0
}

if [ -e /usr/bin/zuul-cloner ]; then
    zuul-cloner --workspace $WORKSPACE $GIT_BASE_URL rdoinfo
else
    # We're outside the gate, just do a regular git clone
    pushd ${WORKSPACE}
    # rm -rf first for idempotency
    rm -rf rdoinfo
    git clone "${GIT_BASE_URL}/rdoinfo" rdoinfo
    popd
fi

echo -n "testing findpkg"

test_rdopkg_findpkg glance                          openstack-glance
test_rdopkg_findpkg glance-distgit                  openstack-glance
test_rdopkg_findpkg openstack-glance                openstack-glance
test_rdopkg_findpkg puppet-glance                   puppet-glance
test_rdopkg_findpkg puppet/puppet-glance            puppet-glance
test_rdopkg_findpkg glanceclient                    python-glanceclient
test_rdopkg_findpkg openstack/glanceclient-distgit  python-glanceclient
test_rdopkg_findpkg python-glanceclient             python-glanceclient

echo 'OK'
