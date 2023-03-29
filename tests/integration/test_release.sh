#!/bin/bash
# Integration tests for "rdopkg release"

set -e

WORKSPACE="${WORKSPACE:-/tmp}"
RDOINFO_URL="https://github.com/redhat-openstack/rdoinfo"


echo "Preparing mocked rdoinfo file"

pushd ${WORKSPACE}
rm -rf rdoinfo
git clone --quiet "$RDOINFO_URL" rdoinfo
cat <<EOF > rdoinfo/rdo-extra.yml
releases:
- name: nobody
  status: development
  branch: rpm-master
  tags_map: separated_buildreqs
  repos:
  - name: el9s
EOF
echo "- rdo-extra.yml" >> rdoinfo/rdo-full.yml
popd


echo "testing \"rdopkg release\""

pushd ${WORKSPACE}
command=$(rdopkg release -l ${WORKSPACE}/rdoinfo -r nobody)
echo "$command" | grep -q "name: nobody"
echo "$command" | grep -q "repos: el9s"
echo "$command" | grep -q "status: development"
popd
echo "...OK!"


echo "testing \"rdopkg release\" for non-existsing release"

pushd ${WORKSPACE}
command2=$(rdopkg release -r foo)
echo "$command2" | grep "No release match your filter."
popd
echo "...OK!"


echo "testing \"rdopkg release -s\" for non-existsing phase"

pushd ${WORKSPACE}
command2=$(rdopkg release -s foo)
echo "$command2" | grep "No release match your phase filter."
popd
echo "...OK!"


echo "testing \"rdopkg release -s\" for existsing phase"

pushd ${WORKSPACE}
command=$(rdopkg release -l ${WORKSPACE}/rdoinfo -s development)
echo "$command" | grep -q "nobody"
popd
echo "...OK!"


echo "testing \"rdopkg release\" with --repo option"

pushd ${WORKSPACE}
rm -rf rdoinfo
git clone --quiet "$RDOINFO_URL" rdoinfo
cat <<EOF > rdoinfo/rdo-extra.yml
releases:
- name: nobody
  status: development
  branch: rpm-master
  tags_map: separated_buildreqs
  repos:
  - name: el-1
EOF
echo "- rdo-extra.yml" >> rdoinfo/rdo-full.yml
command=$(rdopkg release -l ${WORKSPACE}/rdoinfo --repo el-1)
echo "$command" | grep -q -e "repos: el-1"
echo "$command" | grep -c -e "name:" | grep -q 1
popd
echo "...OK!"
