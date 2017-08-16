Feature: rdopkg fix
    Introducing .spec fixes is a core functionality

    Scenario: rdopkg fix
        Given a distgit
        When I run rdopkg fix
        When I add description to .spec chengelog
        When I run rdopkg --continue
        Then .spec file contains new changelog entry with 1 lines
        Then new commit was created
