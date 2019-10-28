#!/bin/bash
# Integration tests for reqcheck

set -e

WORKSPACE="${WORKSPACE:-/tmp}"
RDO_DISTGIT="${WORKSPACE}/rdo_distgit"


rm -rf $RDO_DISTGIT
mkdir -p $RDO_DISTGIT

function test_rdopkg_reqcheck_is_mismatch(){
    pushd ${RDO_DISTGIT}
    if [ ! -d ${RDO_DISTGIT}/$1 ]; then
        rdopkg clone "$1"
    fi
    pushd ${RDO_DISTGIT}/$1
    git checkout origin/$2-rdo
    REQCHECK=$(rdopkg reqcheck -R upstream/stable/$2)
    if [[ $REQCHECK =~ "MISMATCH" ]]; then
        echo "$REQCHECK"
        echo "$0 FAILED EXPECTED: NO VERSION MISMATCH (GOT: MISMATCH)"
        return 1
    fi
    popd
    echo "...OK!"
    popd
    return 0
}

# Test: keep pkg in spec file in a lower version and do not output as MISMATCH
#test_rdopkg_reqcheck_is_mismatch openstack-ceilometer train

test_rdopkg_reqcheck_is_mismatch openstack-panko train
test_rdopkg_reqcheck_is_mismatch openstack-senlin train

rm -rf $RDO_DISTGIT
