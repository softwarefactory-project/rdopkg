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


def test_GerritQuery(monkeypatch):
    mock_result = """{"project":"ironic","branch":"liberty-patches","topic":"p1","id":"Ie0db0345c9d5f9ad3d2ec4880e084cd38d06a6dc","number":"368","subject":"Set default DB location","owner":{"name":"Fabien Boucher","email":"fabien.dot.boucher@gmail.com","username":"morucci"},"url":"http://rpmfactory.beta.rdoproject.org/r/368","commitMessage":"Set default DB location","createdOn":1453933391,"lastUpdated":1456332266,"open":true,"status":"NEW"}
{"type":"stats","rowCount":1,"runTimeMilliseconds":4,"moreChanges":true}"""
    def mock_run(*args, **kwargs):
        return mock_result
    monkeypatch.setattr(utils.cmd, 'run', mock_run)
    g = utils.cmd.GerritQuery('gerrithost', '29418')
    r = g('project:ironic')
    assert(True, isinstance(r, dict))
    assert("Ie0db0345c9d5f9ad3d2ec4880e084cd38d06a6dc",
           r['id'])
    mock_result = """{"type":"stats","rowCount":0,"runTimeMilliseconds":4,"moreChanges":false}"""
    r = g('project:ironic')
    assert(None, r)
