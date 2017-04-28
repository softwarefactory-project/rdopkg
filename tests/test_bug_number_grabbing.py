
from rdopkg.utils.cmd import parse_for_bug_references


def test_patch_parsing_for_rhbz_numbers():
    data = [
        ('Related rhbz: 1433685', 'rhbz#1433685'),
        ('Resolves rhbz: 1433685', 'rhbz#1433685'),
        ('Resolves: rhbz#1433685', 'rhbz#1433685'),
        ('Resolves: rhbz 1433685', 'rhbz#1433685'),
    ]

    # TODO logic here is convoluted as bz does not convey enough information
    # here parse_for_bug_references should probably make it clear it's only
    # looking for rhbz#'s or return qualified rhbz#1234 entries and places
    # that consume it handle that cleanly

    assert('1433685' in parse_for_bug_references('Resolves: rhbz#1433685'))
