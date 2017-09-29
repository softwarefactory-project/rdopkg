Feature: rdopkg fix
    Introducing .spec fixes is a core functionality

    Scenario: rdopkg fix - did not add description of changes
        Given a distgit
        When I run rdopkg fix
        Then rdopkg state file is present

    Scenario: rdopkg fix
        Given a distgit
        When I run rdopkg fix
        When I add description to .spec changelog
        When I run rdopkg --continue
        Then .spec file contains new changelog entry with 1 lines
        Then new commit was created
        Then rdopkg state file is not present
        Then last commit message is:
            """
            foo-bar-1.2.3-3

            Changelog:
            - Description of a change
            """

    Scenario: rdopkg fix - did not add description of changes
        Given a distgit
        When I run rdopkg fix
        When I run rdopkg --continue
        Then command output contains 'Description of changes is missing in %changelog.'
        Then no new commit was created
        Then rdopkg state file is present

    Scenario: rdopkg fix - user reverted all changes
        Given a distgit
        When I run rdopkg fix
        When I undo all changes
        When I run rdopkg --continue
        Then command output contains 'No distgit changes found'
        Then no new commit was created
        Then rdopkg state file is present

    Scenario: rdopkg fix - user aborts
        Given a distgit
        When I run rdopkg fix
        When I undo all changes
        When I run rdopkg --abort
        Then no new commit was created
        Then rdopkg state file is not present

    Scenario: rdopkg fix - Normal semver nvr bumps consistently
        Given a distgit at Version 2.0.0 and Release 0.1
        When I run rdopkg fix
        Then .spec file tag Release is 0.2%{?dist}

    Scenario: rdopkg fix - Normal semver nvr bumps consistently - with dist macro specified
        Given a distgit at Version 2.0.0 and Release 0.1%{?dist}
        When I run rdopkg fix
        Then .spec file tag Release is 0.2%{?dist}

    Scenario: rdopkg fix - Normal semver nvr bumps consistently
        Given a distgit at Version 2.0.0 and Release 1%{?dist}
        When I run rdopkg fix
        Then .spec file tag Release is 2%{?dist}

    Scenario: rdopkg fix - Normal semver nvr bumps consistently
        Given a distgit at Version 2.0.0 and Release 15%{?dist}
        When I run rdopkg fix
        Then .spec file tag Release is 16%{?dist}

    Scenario: rdopkg fix - Normal semver nvr bumps consistently
        Given a distgit at Version 2.0.0 and Release 15.0%{?dist}
        When I run rdopkg fix
        Then .spec file tag Release is 15.1%{?dist}

    Scenario: rdopkg fix - DLRN nvr bumps consistently
        Given a distgit at Version 2.0.0 and Release 0.20170811112938.81363ec%{?dist}
        When I run rdopkg fix
        Then .spec file tag Release is 0.20170811112939%{?dist}

    Scenario: rdopkg fix - DLRN nvr - githash all letters
        Given a distgit at Version 2.0.0 and Release 0.20170811112938.deadbee%{?dist}
        When I run rdopkg fix
        Then .spec file tag Release is 0.20170811112939%{?dist}
