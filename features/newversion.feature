Feature: rdopkg new-version
    Updating package to new version is a core feature

    Scenario: rdopkg new-version --bump-only
        Given a distgit
        When I run rdopkg new-version --bump-only -n 2.1.0
        Then .spec file tag Version is "2.1.0"
        Then .spec file tag Release is "1%{?dist}"
        Then .spec file doesn't contain patches_base
        Then .spec file contains new changelog entry with 1 lines
        Then new commit was created
