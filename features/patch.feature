Feature: rdopkg patch
    Updating patches from patches branch is a core feature

    Scenario: rdopkg patch
        Given a distgit
        Given a patches branch with 5 patches
        When I run rdopkg patch -l
        Then .spec file has 5 patches defined
        Then .spec file doesn't contain patches_base
        Then .spec file contains new changelog entry with 5 lines
        Then new commit was created
        Then last commit message matches:
            """
            foo-bar-[0-9.-]+
            
            Changelog:
            - Original Patch 5
            - Original Patch 4
            - Original Patch 3
            - Original Patch 2
            - Original Patch 1
            """

    Scenario: rdopkg patch --no-bump
        Given a distgit
        Given a patches branch with 3 patches
        When I run rdopkg patch --no-bump -l
        Then .spec file has 3 patches defined
        Then .spec file doesn't contain patches_base
        Then .spec file doesn't contain new changelog entries
        Then new commit was created
        Then last commit message matches:
            """
            Updated patches from master-patches
            """
