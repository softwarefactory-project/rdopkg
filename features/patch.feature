Feature: rdopkg patch
    Updating patches from patches branch is a core feature

    Scenario: rdopkg patch
        Given a distgit at Version 1.20.0 and Release 3
        Given a patches branch with 5 patches
        When I run rdopkg patch -l
        Then command return code is 0
        Then .spec file tag Release is 4%{?dist}
        Then .spec file has 5 patches defined
        Then .spec file doesn't contain patches_base
        Then .spec file contains new changelog entry with 5 lines
        Then .spec file tag Release is 4%{?dist}
        Then new commit was created
        Then git is clean
        Then last commit message is:
            """
            foo-bar-1.20.0-4

            Changelog:
            - Original Patch 5
            - Original Patch 4
            - Original Patch 3
            - Original Patch 2
            - Original Patch 1
            """

    Scenario: rdopkg patch --no-bump
        Given a distgit at Version 1.20.0 and Release 3
        Given a patches branch with 3 patches
        When I run rdopkg patch --no-bump -l
        Then .spec file tag Release is 3%{?dist}
        Then command return code is 0
        Then .spec file has 3 patches defined
        Then .spec file doesn't contain patches_base
        Then .spec file doesn't contain new changelog entries
        Then .spec file tag Release is 3%{?dist}
        Then new commit was created
        Then git is clean
        Then last commit message is:
            """
            Updated patches from master-patches
            """

    Scenario: rdopkg patch --release-bump-index MINOR
        Given a distgit at Version 1.20.0 and Release 1.2.3.lul
        Given a patches branch with 1 patches
        When I run rdopkg patch -l --release-bump-index MINOR
        Then .spec file has 1 patches defined
        Then .spec file contains new changelog entry with 1 lines
        Then .spec file tag Release is 1.3.3.lul%{?dist}
        Then new commit was created

    Scenario: rdopkg patch --release-bump-index 0 (disable release bump)
        Given a distgit at Version 1.20.0 and Release 1.2.3.lul
        Given a patches branch with 1 patches
        When I run rdopkg patch -l --release-bump-index 0
        Then .spec file has 1 patches defined
        Then .spec file contains new changelog entry with 1 lines
        Then .spec file tag Release is 1.2.3.lul%{?dist}
        Then new commit was created

    Scenario: rdopkg patch without version git tag
        Given a distgit
        Given a patches branch with 3 patches without version git tag
        When I run rdopkg patch -l
        Then command return code is 1
        Then no new commit was created
        Then git is clean
        Then rdopkg state file is not present
        Then command output contains 'Invalid base patches branch git reference: '


    Scenario: rdopkg update-patches basic
        Given a distgit at Version 1.0 and Release 23
        Given a patches branch with 3 patches
        When I run rdopkg update-patches
        Then command return code is 0
        Then .spec file tag Release is 23%{?dist}
        Then .spec file has 3 patches defined
        Then .spec file doesn't contain new changelog entries
        Then new commit was created
        Then git is clean
        Then rdopkg state file is not present
        Then command output contains 'Updated patches from master-patches'
        Then command output contains 'Requested distgit update finished, see last commit.'
        Then last commit message is:
            """
            Updated patches from master-patches
            """


    Scenario: rdopkg update-patches noop
        Given a distgit
        Given a patches branch with 0 patches
        When I run rdopkg update-patches
        Then command return code is 0
        Then no new commit was created
        Then git is clean
        Then rdopkg state file is not present
        Then command output contains 'No changes to patches found'

    Scenario: rdopkg patch --amend
        Given a distgit with Change-Id Ideadbeef1234
        Given a patches branch with 5 patches
        When I run rdopkg patch -l --amend
        Then command return code is 0
        Then .spec file tag Release is 3%{?dist}
        Then .spec file has 5 patches defined
        Then .spec file doesn't contain patches_base
        Then .spec file contains new changelog entry with 5 lines
        Then new commit was created
        Then git is clean
        Then last commit message is:
            """
            foo-bar-1.2.3-3

            Changelog:
            - Original Patch 5
            - Original Patch 4
            - Original Patch 3
            - Original Patch 2
            - Original Patch 1

            Change-Id: Ideadbeef1234
            """
