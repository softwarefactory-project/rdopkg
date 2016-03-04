from rdopkg import utils


def test_url_tidying():
    # Do nothing when nothing is provided
    assert(None, utils.tidy_ssh_user())
    # Do nothing when url is not provided
    assert(None, utils.tidy_ssh_user(url=None, user='kyle'))
    # Do nothing when url doesn't start with ssh
    uri = 'http://mygitrepo/myproject.git'
    assert(uri, utils.tidy_ssh_user(uri))
    assert(uri, utils.tidy_ssh_user(uri, user='stan'))
    # Do nothing if url starts with ssh, has no user, and no user provided
    uri = 'ssh://%smygitrepo/myproject.git'
    assert(uri % '', utils.tidy_ssh_user(uri % ''))
    # Add missing user if provided
    assert(uri % 'kenny@', utils.tidy_ssh_user(uri % '', user='kenny'))
    # keep default user if no user provided
    assert(uri % 'cartman@', utils.tidy_ssh_user(uri % 'cartman@'))
    # change default user if user provided
    assert(uri % 'butters@',
           utils.tidy_ssh_user(uri % 'timmy@', user='butters'))
