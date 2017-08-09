Feature: rdopkg actions
    rdopkg is able to run single and multistep actions (commands)

    Scenario: state file doesn't affect new actions
        Given a distgit at Version 1.1.1
        When I run rdopkg new-version
        When I change .spec file tag Version to 2.2.2
        When I run rdopkg pkgenv
        Then command output contains 'Version:\s+2.2.2'
