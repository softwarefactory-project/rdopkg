from rdopkg.utils.issues import search_bug_references
import pytest


def test_patch_parsing_for_rhbz_numbers():
    data = [
        ('Resolves: rhbz#1433685', 'rhbz#1433685', 1433685),
        ('Related: rhbz#1433685', 'rhbz#1433685', 1433685),
        ('  Related:   \t  rhbz#1433685  ', 'rhbz#1433685', 1433685),
    ]

    # TODO logic here is convoluted as bz does not convey enough information
    # here search_bug_references should probably make it clear it's only
    # looking for rhbz#'s or return qualified rhbz#1234 entries and places
    # that consume it handle that cleanly

    for text, _, expected in data:
        assert str(expected) in search_bug_references(text)


def test_patch_parsing_no_input():
    assert not search_bug_references('')


def test_patch_parsing_input_None():
    assert not search_bug_references(None)


def test_patch_parsing_no_bug_data_to_be_found():
    assert not search_bug_references(' foo bar blah bug found 1324')


@pytest.mark.skip(
    'unhandled content seen in wild that could be parsed for bug numbers')
def test_patch_parsing_for_rhbz_numbers_bad_seen_in_wild():
    data_variants_seen_in_wild = [
        ('Related rhbz: 1433685', 'rhbz#1433685', 1433685),
        ('Resolves rhbz: 1433685', 'rhbz#1433685', 1433685),
        ('Resolves: rhbz 1433685', 'rhbz#1433685', 1433685),
        ('Resolves: rhbz# 1433685', 'rhbz#1433685', 1433685),
        ('Resolves: rhbz #1433685', 'rhbz#1433685', 1433685),
    ]

    for text, _, expected in data_variants_seen_in_wild:
        assert str(expected) in search_bug_references(text)
