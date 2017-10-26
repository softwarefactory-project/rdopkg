Feature: rdopkg pkgenv
    Displaying package environment details is a core feature.

    Scenario: rdopkg pkgenv basic usage
        Given a distgit at Version 1.0.0 and Release 0.1
        Given a patches branch with 2 patches
        When I run rdopkg pkgenv
        Then command output contains 'Patches style:\s+branch'
        Then command output contains 'Patches base:\s+1.0.0 : existing git tag'
        Then command output contains 'Version:\s+1.0.0'
        Then command output contains 'VR:\s+1:1.0.0-0.1'
        Then command output contains 'Local patches branch:\s+master-patches : \w+'
        Then no new commit was created

    Scenario: rdopkg pkgenv without version tag and patches branch
        Given a distgit at Version 0.1 and Release 2
        When I run rdopkg pkgenv
        Then command output contains 'VR:\s+1:0.1-2'
        Then command output contains 'Local patches branch:\s+master-patches : not found'
        Then command output contains 'Patches base:\s+0.1 : invalid git reference'

    Scenario: rdopkg pkgenv with valid patches_base
        Given a distgit at Version 23 and Release 69
        Given a patches branch with 2 patches
        When I set .spec file patches_base to existing commit +42
        When I run rdopkg pkgenv
        Then command output contains 'Version:\s+23'
        Then command output contains 'VR:\s+1:23-69'
        Then command output contains 'Local patches branch:\s+master-patches : \w+'
        Then command output contains 'Patches base:\s+\w+\+42 : existing git commit'

    Scenario: rdopkg pkgenv with invalid patches_base
        Given a distgit at Version 0 and Release 0
        Given a patches branch with 2 patches
        When I set .spec file patches_base=OVER+9000
        When I run rdopkg pkgenv
        Then command output contains 'Version:\s+0'
        Then command output contains 'VR:\s+1:0-0'
        Then command output contains 'Patches base:\s+OVER\+9000 : invalid git reference'
