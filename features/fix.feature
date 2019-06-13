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

    Scenario: rdopkg fix - user reruns
        Given a distgit
        When I run rdopkg fix
        When I run rdopkg fix
        Then command output contains 'You're in the middle of previous action: fix'
        Then command output contains 'Please `--continue` or `--abort`'
        Then no new commit was created
        Then rdopkg state file is present

    Scenario: rdopkg fix - user aborts and reruns
        Given a distgit
        When I run rdopkg fix
        When I run rdopkg fix
        When I undo all changes
        When I run rdopkg --abort
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

    Scenario Outline: rdopkg fix - DLRN Release <fmt>.date.hash - <case> hash
        Given a distgit at Version 2.0.0 and Release <old release>
        When I run rdopkg fix
        Then .spec file tag Release is <new release>

        Examples: 0.date.hash
            | fmt | case        | old release                      | new release                      |
            | 0   | mixed       | 0.20170811112938.81363ec%{?dist} | 0.20170811112939.81363ec%{?dist} |
            | 0   | all letters | 0.20170811112938.deadbee%{?dist} | 0.20170811112939.deadbee%{?dist} |
            | 0   | all numbers | 0.20170811112938.8136333%{?dist} | 0.20170811112939.8136333%{?dist} |

        Examples: 0.1.date.hash
            | fmt | case        | old release                         | new release                         |
            | 0.1 | mixed       | 0.1.20170811112938.81363ec%{?dist}  | 0.2.20170811112938.81363ec%{?dist}  |
            | 0.1 | all letters | 0.1.20170811112938.deadbee%{?dist}  | 0.2.20170811112938.deadbee%{?dist}  |
            | 0.1 | all numbers | 0.22.20170811112938.8136333%{?dist} | 0.23.20170811112938.8136333%{?dist} |

    Scenario Outline: rdopkg fix --release-bump-index <index>
        Given a distgit at Version 10.20.30 and Release <old release>
        When I run rdopkg fix --release-bump-index <index>
        Then .spec file tag Release is <new release>

        Examples: correct bump-Nth-part indexes
            | index | old release   | new release       |
            | major | 0.1.2         | 1.1.2%{?dist}     |
            | MINOR | 10.20.30      | 10.21.30%{?dist}  |
            | PaTcH | 0.0.0%{?dist} | 0.0.1%{?dist}     |
            | 1     | 1000%{?dist}  | 1001%{?dist}      |
            | 2     | 10.20%{?dist} | 10.21%{?dist}     |
            | 3     | 1.2.3.4.5     | 1.2.4.4.5%{?dist} |
            | 5     | 1.2.3.4.5     | 1.2.3.4.6%{?dist} |
            | 0     | 23.23.23      | 23.23.23%{?dist}  |

    Scenario Outline: rdopkg fix --release-bump-index <index> - invalid indexes
        Given a distgit at Version 10 and Release <release>
        When I run rdopkg fix -R <index>
        Then command output contains '<error>'

        Examples: invalid strategies
            | index | release | error |
            | minor | 1.lul.1 | Invalid Release bump index: 2. part of Release '\S+' isn't numeric: lul |
            | PATCH | 1.2     | Invalid Release bump index: 3 |
            | 1337  | 1.2.3   | Invalid Release bump index: 1337 \(Release: 1.2.3\) |
