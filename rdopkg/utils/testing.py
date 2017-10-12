import difflib


def exdiff(txt1, txt2, header=None):
    d = difflib.ndiff(txt1.splitlines(1), txt2.splitlines(2))
    s = ''.join(list(d))
    if header:
        s = "%s\n%s" % (header, s)
    # python 2 exceptions fail with unicode chars (?!)
    s = s.encode('ascii', 'replace')
    return s
