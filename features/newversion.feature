Feature: rdopkg new-version
    Updating package to new version is a core feature

    Scenario: rdopkg new-version --bump-only
        Given a distgit at Version 2.0.0 and Release 3
        When I run rdopkg new-version --bump-only -n 2.1.0
        Then command output contains 'Action finished'
        Then .spec file tag Version is 2.1.0
        Then .spec file tag Release is 1%{?dist}
        Then .spec file doesn't contain patches_base
        Then .spec file contains new changelog entry with 1 lines
        Then new commit was created
        Then last commit message matches:
            """
            foo-bar-2.1.0-1
            
            Changelog:
            - Update to 2.1.0
            """

    Scenario: rdopkg new-version with upstream patches
        Given a distgit at Version 0.1 and Release 0.1
        Given a patches branch with 5 patches
        Given a new version 1.0.0 with 2 patches from patches branch
        When I run rdopkg new-version -lntU 1.0.0
        Then command output contains 'Action finished'
        Then .spec file tag Version is 1.0.0
        Then .spec file tag Release is 1%{?dist}
        Then .spec file doesn't contain patches_base
        Then .spec file has 3 patches defined
        Then .spec file contains new changelog entry with 1 lines
        Then new commit was created

    Scenario: rdopkg new-version --bump-only --bug
        Given a distgit at Version 2.0.0 and Release 3
        When I run rdopkg new-version --bump-only -n 2.1.0 --bug rhbz#12345
        Then command output contains 'Action finished'
        Then .spec file contains new changelog entry with rhbz#12345
        Then new commit was created
        Then commit message contains rhbz#12345

    Scenario: rdopkg new-version --bump-only -H
        Given a distgit at Version 2.0.0 and Release 3
        Given a local file commitmsg containing "Testing Alternate Commit Header"
        When I run rdopkg new-version --bump-only -n 2.1.0 -H commitmsg
        Then command output contains 'Action finished'
        Then new commit was created
        Then commit message contains Testing Alternate Commit Header
