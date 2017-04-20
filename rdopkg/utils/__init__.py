import re


def tidy_ssh_user(url=None, user=None):
    """make sure a git repo ssh:// url has a user set"""
    if url and url.startswith('ssh://'):
        # is there a user already ?
        match = re.compile('ssh://([^@]+)@.+').match(url)
        if match:
            ssh_user = match.group(1)
            if user and ssh_user != user:
                # assume prevalence of argument
                url = url.replace(re.escape(ssh_user) + '@',
                                  user + '@')
        elif user:
            url = 'ssh://' + \
                  user + '@' + \
                  url[len('ssh://'):]
    return url
