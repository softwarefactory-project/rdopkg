#!/bin/bash
# Integration tests for "rdopkg release"

set -e

WORKSPACE="${WORKSPACE:-/tmp}"
RDOINFO_URL="https://github.com/redhat-openstack/rdoinfo"

echo "testing \"rdopkg release\""

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
