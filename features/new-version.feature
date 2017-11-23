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
        Then git is clean
        Then last commit message is:
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
        Then git is clean
        Then last commit message is:
            """
            foo-bar-1.0.0-1

            Changelog:
            - Update to 1.0.0
            """

    Scenario: rdopkg new-version --bump-only --bug <id>
        Given a distgit at Version 2.0.0 and Release 3
        When I run rdopkg new-version --bump-only -n 2.1.0 --bug rhbz#12345
        Then command output contains 'Action finished'
        Then .spec file contains new changelog entry with rhbz#12345
        Then new commit was created
        Then git is clean
        Then last commit message contains rhbz#12345
        Then last commit message is:
            """
            foo-bar-2.1.0-1

            Changelog:
            - Update to 2.1.0 (rhbz#12345)

            Resolves: rhbz#12345
            """

    Scenario: rdopkg new-version --bump-only --commit-header-file <file>
        Given a distgit at Version 2.0.0 and Release 3
        Given a local file commitmsg containing "Testing Alternate Commit Header"
        When I run rdopkg new-version --bump-only -n --commit-header-file commitmsg 2.1.0
        Then command output contains 'Action finished'
        Then new commit was created
        Then git is clean
        Then last commit message is:
            """
            Testing Alternate Commit Header

            Changelog:
            - Update to 2.1.0
            """

    Scenario: rdopkg new-version --bump-only --bug <id> -H <file>
        Given a distgit at Version 2.0.0 and Release 3
        Given a local file commitmsg:
            """
            Testing

            Multiline
            Commit
            Header
            """
        When I run rdopkg new-version --bump-only -n --bug rhbz#12345,rhbz#232323 -H commitmsg 2.1.0
        Then command output contains 'Action finished'
        Then .spec file contains new changelog entry with rhbz#12345
        Then .spec file contains new changelog entry with rhbz#232323
        Then new commit was created
        Then git is clean
        Then last commit message contains rhbz#12345
        Then last commit message contains rhbz#232323
        Then last commit message is:
            """
            Testing

            Multiline
            Commit
            Header

            Changelog:
            - Update to 2.1.0 (rhbz#12345,rhbz#232323)

            Resolves: rhbz#12345
            Resolves: rhbz#232323
            """

    Scenario: rdopkg new-version without starting version git tag
        Given a distgit at Version 0.1 and Release 0.1
        Given a patches branch with 2 patches without version git tag
        When I run rdopkg new-version -l 1.0.0
        Then no new commit was created
        Then git is clean
        Then command output contains 'Invalid base patches branch git reference:'

    Scenario: rdopkg new-version without new version git tag
        Given a distgit at Version 0.1 and Release 0.1
        Given a patches branch with 2 patches
        When I run rdopkg new-version -l 2.2.2
        Then no new commit was created
        Then git is clean
        Then command output contains 'Invalid git reference: 2.2.2'
