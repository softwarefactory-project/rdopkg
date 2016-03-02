import re


def tidy_ssh_user(url, user):
    """make sure a git repo ssh:// url has a user set"""
    if url.startswith('ssh://'):
        #is there a user already ?
        match = re.compile('ssh://([^@]+)@.+').match(url)
        if match:
            ssh_user = match.groups()[0]
            if ssh_user != user:
                # assume prevalence of argument
                url.replace(ssh_user + '@',
                            user + '@')
        else:
            url = 'ssh://' +\
                   user + '@' +\
                   url[len('ssh://'):]
    return url
