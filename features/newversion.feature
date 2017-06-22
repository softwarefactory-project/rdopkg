Feature: rdopkg new-version
    Updating package to new version is a core feature

    Scenario: rdopkg new-version --bump-only
        Given a temporary directory
        Given a distgit
        When I run rdopkg new-version --bump-only -n 2.1.0
        Then .spec file tag Version is "2.1.0"
        Then .spec file tag Release is "1%{?dist}"
        Then .spec file doesn't contain patches_base
        Then new commit was created
