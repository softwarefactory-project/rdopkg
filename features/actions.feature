Feature: rdopkg actions
    rdopkg is able to run single and multistep actions (commands)

    Scenario: state file doesn't affect new actions
        Given a distgit at Version 1.1.1
        When I run rdopkg new-version
        When I change .spec file tag Version to 2.2.2
        When I run rdopkg pkgenv
        Then command output contains 'Version:\s+2.2.2'

    Scenario: assume .spec does not containe patches_base by default
        Given a distgit at Version 1.1.1
        Then .spec file doesn't contain patches_base
        Then .spec file doesn't contain patches_ignore

    Scenario: add magic_comment patches_base when already_set
        Given a distgit at Version 1.1.1
        Then .spec file doesn't contain patches_base
        When I run rdopkg set-magic-comment patches_base foo
        Then .spec file contains patches_base=foo
        When I run rdopkg set-magic-comment patches_base v1.1.1
        Then .spec file contains patches_base=v1.1.1

    Scenario: add magic_comment patches_base empty when already set
        Given a distgit at Version 1.1.1
        Then .spec file doesn't contain patches_base
        When I run rdopkg set-magic-comment patches_base foo
        Then .spec file contains patches_base=foo
        When I run rdopkg set-magic-comment patches_base ''
        Then .spec file contains patches_base=

    Scenario: add magic_comment patches_base and patches_ignore when not present
        Given a distgit at Version 1.1.1
        When I run rdopkg set-magic-comment patches_base v1.1.1
        Then .spec file contains patches_base=v1.1.1
        When I run rdopkg set-magic-comment patches_ignore DROP-IN-RPM
        Then .spec file contains patches_ignore

    Scenario: add magic_comment only patches_ignore
        Given a distgit at Version 1.1.1
        Then .spec file doesn't contain patches_base
        Then .spec file doesn't contain patches_ignore
        When I run rdopkg set-magic-comment patches_ignore DROP-IN-RPM
        Then .spec file contains patches_ignore

    Scenario: set magic_comment to empty string
        Given a distgit at Version 1.1.1
        Then .spec file doesn't contain patches_base
        Then .spec file doesn't contain patches_ignore
        When I run rdopkg set-magic-comment patches_ignore  ''
        Then .spec file doesn't contain patches_ignore
