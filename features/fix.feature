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

    Scenario: rdopkg fix - Release with %{?dist} in the middle bumps correctly
        Given a distgit at Version 2.0.0 and Release 1.0%{?dist}.1
        When I run rdopkg fix
        Then .spec file tag Release is 1.1%{?dist}.1

    Scenario: rdopkg fix - DLRN nvr bumps consistently
        Given a distgit at Version 2.0.0 and Release 0.20170811112938.81363ec%{?dist}
        When I run rdopkg fix
        Then .spec file tag Release is 0.20170811112939%{?dist}

    Scenario: rdopkg fix - DLRN nvr - githash all letters
        Given a distgit at Version 2.0.0 and Release 0.20170811112938.deadbee%{?dist}
        When I run rdopkg fix
        Then .spec file tag Release is 0.20170811112939%{?dist}

    Scenario Outline: rdopkg fix --release-bump-strategy <strategy>
        Given a distgit at Version 10.20.30 and Release <old release>
        When I run rdopkg fix --release-bump-strategy <strategy>
        Then .spec file tag Release is <new release>

        Examples: correct bump-Nth-part strategies
            | strategy | old release   | new release       |
            | 3        | 1.2.3.4.5     | 1.2.4.4.5%{?dist} |
            | 2        | 10.20%{?dist} | 10.21%{?dist}     |
            | 1        | 1000%{?dist}  | 1001%{?dist}      |

    Scenario Outline: rdopkg fix --release-bump-strategy <strategy> - invalid strategies
        Given a distgit at Version 10 and Release <release>
        When I run rdopkg fix -R <strategy>
        Then command output contains '<error>'

        Examples: invalid strategies
            | strategy | release | error             |
            | 0        | 1       | Invalid release bump strategy: 0 \(positive integer required\) |
            | 2        | 1.lul.1 | Invalid release bump strategy: 2. part of Release '\S+' isn't numeric: lul |
            | 3        | 1.2     | Invalid Release part index: 3    |
            | 1337     | 1.2.3   | Invalid Release part index: 1337 |
