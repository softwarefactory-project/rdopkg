import pytest
from rdopkg import guess
from rdopkg import exception


def test_guess_release():
    cases = [
        ('el6-folsom', 'folsom'),
        ('rh-grizzly-rhel-6', 'grizzly'),
        ('rhos-4.0-rhel-7', 'havana'),
        ('stable/icehouse', 'icehouse'),
        ('f19', 'grizzly'),
        ('f20', 'havana'),
        ('f21', 'icehouse'),
        ('f22', 'juno'),
        # XXX: moving part (will need update on new Fedora)
        ('master', 'kilo'),
    ]
    for branch, rls in cases:
        grls = guess.osrelease(branch)
        assert grls == rls, ('guessed release for \'%s\': %s '
                             '(should be %s)' % (branch, grls, rls))

    with pytest.raises(exception.CantGuess):
        grls = guess.osrelease('')
    with pytest.raises(exception.CantGuess):
        grls = guess.osrelease('wololo')


def test_guess_dist():
    cases = [
        ('el6-havana', 'epel-6'),
        ('icehouse-epel7', 'epel-7'),
        ('icehouse-epel-7', 'epel-7'),
        ('rh-grizzly-rhel-6', 'rhel-6'),
        ('rhos-4.0-rhel-7', 'rhel-7'),
        ('f19', 'fedora-18'),
        ('f20', 'fedora-19'),
        ('f21', 'fedora-20'),
        # XXX: moving part (will need update on new Fedora)
        ('master', 'fedora-21'),
    ]
    for branch, dist in cases:
        gdist = guess.dist(branch)
        assert gdist == dist, ('guessed dist for \'%s\': %s '
                               '(should be %s)' % (branch, gdist, dist))

    with pytest.raises(exception.CantGuess):
        dist = guess.dist('')
    with pytest.raises(exception.CantGuess):
        dist = guess.dist('wololo')
