Feature: rdopkg pkgenv
    Displaying package environment details is a core feature.

    Scenario: rdopkg pkgenv basic usage
        Given a distgit at Version 1.0.0 and Release 0.1
        Given a patches branch with 2 patches
        When I run rdopkg pkgenv
        Then command output contains 'Patches style:\s+branch'
        Then command output contains 'Patches base:\s+N/A'
        Then command output contains 'Patches base ref:\s+1.0.0 : existing git tag'
        Then command output contains 'Version:\s+1.0.0'
        Then command output contains 'VR:\s+1:1.0.0-0.1'
        Then command output contains 'Release style:\s+generic'
        Then command output contains 'Rls bump index:\s+last-numeric'
        Then command output contains 'Local patches branch:\s+master-patches : \w+'
        Then no new commit was created

    Scenario: rdopkg pkgenv without version tag and patches branch
        Given a distgit at Version 0.1 and Release 2
        When I run rdopkg pkgenv
        Then command output contains 'VR:\s+1:0.1-2'
        Then command output contains 'Patches base:\s+N/A'
        Then command output contains 'Patches base ref:\s+0.1 : invalid git reference'
        Then command output contains 'Local patches branch:\s+master-patches : not found'

    Scenario: rdopkg pkgenv with valid patches_base
        Given a distgit at Version 23 and Release 69
        Given a patches branch with 2 patches
        When I set .spec file patches_base to existing commit +42
        When I run rdopkg pkgenv
        Then command output contains 'Version:\s+23'
        Then command output contains 'VR:\s+1:23-69'
        Then command output contains 'Patches base:\s+\w+\+42'
        Then command output contains 'Patches base ref:\s+\w+ : existing git commit'
        Then command output contains 'Local patches branch:\s+master-patches : \w+'

    Scenario: rdopkg pkgenv with invalid patches_base
        Given a distgit at Version 0 and Release 0
        Given a patches branch with 2 patches
        When I set .spec file patches_base=OVER+9000
        When I run rdopkg pkgenv
        Then command output contains 'Version:\s+0'
        Then command output contains 'VR:\s+1:0-0'
        Then command output contains 'Patches base:\s+OVER\+9000'
        Then command output contains 'Patches base ref:\s+OVER : invalid git reference'

    Scenario Outline: rdopkg pkgenv - DLRN Release <fmt>.date.hash - <case> hash
        Given a distgit at Version 2.0.0 and Release <release>
        When I run rdopkg pkgenv
        Then command output contains 'Release style:\s+DLRN <fmt>.date.hash'
        Then command output contains 'Rls bump index:\s+2 / MINOR'

        Examples: 0.date.hash
            | fmt | case        | release                          |
            | 0   | mixed       | 0.20170811112938.81363ec%{?dist} |
            | 0   | all letters | 0.20170811112938.deadbee         |
            | 0   | all numbers | 0.20170811112938.8136333%{?dist} |

        Examples: 0.1.date.hash
            | fmt | case        | release                             |
            | 0.1 | mixed       | 0.1.20170811112938.81363ec%{?dist}  |
            | 0.1 | all letters | 0.1.20170811112938.deadbee%{?dist}  |
            | 0.1 | all numbers | 0.22.20170811112938.8136333         |
