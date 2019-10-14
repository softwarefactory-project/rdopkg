from __future__ import unicode_literals

import codecs
from collections import defaultdict
import os
import re
import time

from rdopkg import exception
from rdopkg.utils import lint

RPM_AVAILABLE = False
try:
    import rpm
    RPM_AVAILABLE = True
except ImportError:
    pass


RELEASE_PARTS_SEMVER = {
    'MAJOR': 1,
    'MINOR': 2,
    'PATCH': 3,
}


def split_filename(filename):
    """
    Received a standard style rpm fullname and returns
    name, version, release, epoch, arch
    Example: foo-1.0-1.i386.rpm returns foo, 1.0, 1, i386
             1:bar-9-123a.ia64.rpm returns bar, 9, 123a, 1, ia64

    This function replaces rpmUtils.miscutils.splitFilename, see
    https://bugzilla.redhat.com/1452801
    """

    # Remove .rpm suffix
    if filename.endswith('.rpm'):
        filename = filename.split('.rpm')[0]

    # is there an epoch?
    components = filename.split(':')
    if len(components) > 1:
        epoch = components[0]
    else:
        epoch = ''

    # Arch is the last item after .
    arch = filename.rsplit('.')[-1]
    remaining = filename.rsplit('.%s' % arch)[0]
    release = remaining.rsplit('-')[-1]
    version = remaining.rsplit('-')[-2]
    name = '-'.join(remaining.rsplit('-')[:-2])

    return name, version, release, epoch, arch


def string_to_version(verstring):
    """
    Return a tuple of (epoch, version, release) from a version string

    This function replaces rpmUtils.miscutils.stringToVersion, see
    https://bugzilla.redhat.com/1364504
    """
    # is there an epoch?
    components = verstring.split(':')
    if len(components) > 1:
        epoch = components[0]
    else:
        epoch = 0

    remaining = components[:2][0].split('-')
    version = remaining[0]
    release = remaining[1]

    return (epoch, version, release)


def spec_fn(spec_dir='.'):
    """
    Return the filename for a .spec file in this directory.
    """
    specs = [f for f in os.listdir(spec_dir)
             if os.path.isfile(f) and f.endswith('.spec')]
    if not specs:
        raise exception.SpecFileNotFound()
    if len(specs) != 1:
        raise exception.MultipleSpecFilesFound()
    return specs[0]


def get_patches_from_files(patches_dir='.'):
    patches_fns = [f for f in os.listdir(patches_dir)
                   if os.path.isfile(f) and f.endswith('.patch')]
    if not patches_fns:
        return []
    patches = []
    for pfn in patches_fns:
        with codecs.open(pfn, 'r', encoding='utf-8') as fp:
            txt = fp.read()
        hash = None
        m = re.search(r'^From ([a-z0-9]+)', txt, flags=re.M)
        if m:
            hash = m.group(1)
        subj = None
        m = re.search(r'^Subject:\w*(.+)$', txt, flags=re.M)
        if m:
            subj = m.group(1)
        patches.append((pfn, hash, subj))
    return patches


def version_parts(version):
    """
    Split a version string into numeric X.Y.Z part and the rest (milestone).
    """
    m = re.match(r'(\d+(?:\.\d+)*)([.%]|$)(.*)', version)
    if m:
        numver = m.group(1)
        rest = m.group(2) + m.group(3)
        return numver, rest
    else:
        return version, ''


def release_parts(version):
    """
    Split RPM Release string into (numeric X.Y.Z part, milestone, rest).

    :returns: a three-element tuple (number, milestone, rest). If we cannot
              determine the "milestone" or "rest", those will be an empty
              string.
    """
    numver, tail = version_parts(version)
    if numver and not re.match(r'\d', numver):
        # entire release is macro a la %{release}
        tail = numver
        numver = ''
    m = re.match(r'(\.?(?:%\{\?milestone\}|[^%.]+))(.*)$', tail)
    if m:
        milestone = m.group(1)
        rest = m.group(2)
    else:
        milestone = ''
        rest = tail
    return numver, milestone, rest


def has_macros(s):
    # detect escaping (%%)
    rex = r'.*(?<!%)%[\w{].*'
    if re.match(rex, s):
        return True
    return False


def nvrcmp(nvr1, nvr2):
    if not RPM_AVAILABLE:
        raise exception.RpmModuleNotAvailable()
    t1 = string_to_version(nvr1)
    t2 = string_to_version(nvr2)
    return rpm.labelCompare(t1, t2)


def vcmp(v1, v2):
    if not RPM_AVAILABLE:
        raise exception.RpmModuleNotAvailable()
    t1 = ('0', v1, '')
    t2 = ('0', v2, '')
    return rpm.labelCompare(t1, t2)


def nvr2version(nvr):
    _, v, _, _, _ = split_filename(nvr)
    return v


class Spec(object):
    """
    Lazy .spec file parser and editor.
    """

    RE_PATCH = r'(?:^|\n)(Patch\d+:)'
    RE_AFTER_SOURCES = r'((?:^|\n)Source\d*:[^\n]*\n\n?)'
    RE_AFTER_MAGIC_COMMENTS = (
        r'((?:^|\n)(?:#[ \t]*\n)*#\s*[\D_]*\s*=[^\n]*\n(?:#[ '
        r'\t]*\n)*)\n*')
    RE_IN_MAGIC_COMMENTS = (
        r'((?:^|\n)(?:#[ \t]*\n)*)(#\s*[^0-9\n]*\s*=[^\n]*\n)')
    RE_MACRO_BASE = r'%global\s+{0}\s+'

    def __init__(self, fn=None, txt=None):
        """
        Spec file reader/writer/parser.

        :param  fn: The filename of a .spec file. If not provided, we will
                    select the only .spec file in current directory or throw an
                    exception when multiple or no .spec files are present.
        :type   fn: ``str``

        :param txt: The textual contents of a .spec file. If not provided, we
                    will read the contents from disk.
        :type  txt: ``str``
        """
        self._fn = fn
        self._txt = txt
        self._rpmspec = None

    @property
    def fn(self):
        """ The filename of this .spec file. """
        if not self._fn:
            self._fn = spec_fn()
        return self._fn

    @property
    def txt(self):
        """ The textual contents of this .spec file. """
        if not self._txt:
            with codecs.open(self.fn, 'r', encoding='utf-8') as fp:
                self._txt = fp.read()
        return self._txt

    def load_rpmspec(self):
        if not RPM_AVAILABLE:
            raise exception.RpmModuleNotAvailable()
        rpm.addMacro('_sourcedir',
                     os.path.dirname(os.path.realpath(self.fn)))
        try:
            self._rpmspec = rpm.spec(self.fn)
        except ValueError as e:
            raise exception.SpecFileParseError(spec_fn=self.fn,
                                               error=e.args[0])

    @property
    def rpmspec(self):
        if not self._rpmspec:
            self.load_rpmspec()
        return self._rpmspec

    def expand_macro(self, macro):
        if not self._rpmspec:
            self.load_rpmspec()
        if not RPM_AVAILABLE:
            raise exception.RpmModuleNotAvailable()
        return rpm.expandMacro(macro)

    def get_tag(self, tag, default=exception.SpecFileParseError,
                expand_macros=False):
        m = re.search(r'^%s:\s+(\S.*)$' % tag, self.txt, re.M)
        if not m:
            if default != exception.SpecFileParseError:
                return default
            raise exception.SpecFileParseError(spec_fn=self.fn,
                                               error="%s tag not found" % tag)
        tag = m.group(1).rstrip()
        if expand_macros and has_macros(tag):
            # don't parse using rpm unless required
            tag = self.expand_macro(tag)
        return tag

    def set_tag(self, tag, value):
        self._txt, n = re.subn(r'^(%s:\s+).*$' % re.escape(tag),
                               r'\g<1>%s' % value, self.txt, flags=re.M)
        return n > 0

    def get_tag_align_ws(self, tag):
        if not tag.endswith(':'):
            tag += ':'
        m = re.search(r'^%s(\s*)' % re.escape(tag), self.txt, flags=re.M)
        if not m:
            return ''
        return m.group(1)

    def get_magic_comment(self, name, expand_macros=False):
        """Return a value of # name=value comment in spec or None."""
        match = re.search(r'^#\s*?%s\s?=\s?(\S+)' % re.escape(name),
                          self.txt, flags=re.M)
        if not match:
            return None

        val = match.group(1)
        if expand_macros and has_macros(val):
            # don't parse using rpm unless required
            val = self.expand_macro(val)
        return val

    def _create_new_magic_comment(self, name, value):
        # check to see if we have any magic comments in right slot
        # after SourceX and before Patch Y - if so insert at begining block
        # otherwise insert a new block as before

        if re.findall(self.RE_IN_MAGIC_COMMENTS, self._txt, flags=re.M):
            self._txt = re.sub(
                self.RE_IN_MAGIC_COMMENTS,
                r'\g<1># %s=%s\n\g<2>' % (name, value),
                self.txt, count=1, flags=re.M)
            return

        self._txt, n = re.subn(
            self.RE_PATCH,
            r'\n#\n# %s=%s\n#\n\g<1>' % (name, value),
            self.txt, count=1, flags=re.M)
        if n != 1:
            self._txt, n = re.subn(
                self.RE_AFTER_SOURCES,
                r'\g<1>#\n# %s=%s\n#\n\n' % (name, value),
                self.txt, count=1, flags=re.M)
            if n != 1:
                raise exception.SpecFileParseError(
                    spec_fn=self.fn,
                    error="Unable to create new #%s magic comment." % name)

    def set_magic_comment(self, name, value):
        """Set a magic comment like # name=value in the spec."""
        present = self.get_magic_comment(name)

        if value is None or value == '':
            print("Dropping")
            # Drop magic comment patches_base and following empty comments
            self._txt = re.sub(
                r'(?:^#)*\s*%s\s*=[^\n]*\n(?:#\n)*' % re.escape(name),
                '', self.txt, flags=re.M)
            return

        if present is None:
            return self._create_new_magic_comment(name, value)
        else:
            # Just replace it
            self._txt, count = re.subn(
                r'(?:#\n)*'
                + r'(^#\s*%s\s*=[\t ]?)[^\n]*\n(?:#\n)*' % re.escape(name),
                r'\g<1>%s\n' % value, self.txt, flags=re.M)

            # if there are duplicates drop one of them
            if count > 1:
                self._txt, count = re.subn(
                    r'(#\s?%s\s?=\s?)\S*' % re.escape(name),
                    '', self.txt, count=count - 1, flags=re.M)
                count = 1
            # check to make sure we have only one
            if count == 0:
                raise exception.SpecFileParseError(
                    spec_fn=self.fn,
                    error="Unable to set #%s" % name)
            elif count > 1:
                raise exception.SpecFileParseError(
                    spec_fn=self.fn,
                    error="Multiple magic comments #{0}".format(name))

    def get_patches_base(self, expand_macros=False):
        """Return a tuple (version, number_of_commits) that are parsed
        from the patches_base in the specfile.
        """
        patches_base = self.get_magic_comment('patches_base')
        if patches_base is None:
            return None, 0

        if expand_macros and has_macros(patches_base):
            # don't parse using rpm unless required
            patches_base = self.expand_macro(patches_base)
        patches_base_ref, _, n_commits = patches_base.partition('+')

        try:
            n_commits = int(n_commits)
        except ValueError:
            n_commits = 0
        return patches_base_ref, n_commits

    def get_patches_ignore_regex(self):
        """Returns a string representing a regex for filtering out patches

        This string is parsed from a comment in the specfile that contains the
        word filter-out followed by an equal sign.

        For example, a comment as such:
            # patches_ignore=(regex)

        would mean this method returns the string '(regex)'

        Only a very limited subset of characters are accepted so no fancy stuff
        like matching groups etc.
        """
        regex_string = self.get_magic_comment('patches_ignore')
        if regex_string is None:
            return None
        try:
            return re.compile(regex_string)
        except Exception:
            return None

    def set_patches_base(self, base):
        if not base and re.search(r'^#\s*patches_ignore\s*=\s*\S+',
                                  self.txt, flags=re.M):
            # This is a temporary hack as patches_ignore currently requires
            # explicit patches_base. This should be solved with a proper
            # magic comment parser and using Version in filtration logic
            # when no patches_base is defined.
            base = self.get_tag('Version', expand_macros=True)

        self.set_magic_comment('patches_base', base)

    def set_patches_base_version(self, version, ignore_macros=True):
        if not version:
            version = ''
        old_pb, n_commits = self.get_patches_base()
        if (ignore_macros and old_pb and has_macros(old_pb)):
            return False
        if n_commits > 0:
            version += ("+%s" % n_commits)
        self.set_patches_base(version)
        return True

    def get_n_patches(self):
        return len(re.findall(r'^Patch[0-9]+:', self.txt, re.M))

    def get_n_excluded_patches(self):
        """
        Gets number of excluded patches from patches_base:
        #patches_base=1.0.0+THIS_NUMBER
        """
        _, n_commits = self.get_patches_base()
        return n_commits

    def get_patch_fns(self):
        fns = []
        for m in re.finditer(r'^\s*Patch\d+:\s*(\S+)\s*$', self.txt,
                             flags=re.M):
            fns.append(m.group(1))
        return fns

    def wipe_patches(self):
        self._txt = re.sub(r'\n+(?:(?:Patch|.patch)\d+[^\n]*)', '', self.txt)

    def sanity_check(self):
        hints = lint.lint(self.fn, checks=['sanity'])
        lint.lint_report(hints, error_level='E')

    def patches_apply_method(self):
        if '\ngit am %{patches}' in self.txt:
            return 'git-am'
        if '\n%autosetup' in self.txt:
            return 'autosetup'
        return 'rpm'

    def set_commit_ref_macro(self, ref):
        self._txt = re.sub(
            r'^\%global commit \w+',
            '%%global commit %s' % ref, self.txt, flags=re.M)

    def set_new_patches(self, fns):
        self.wipe_patches()
        if not fns:
            return
        apply_method = self.patches_apply_method()
        ps = ''
        pa = ''
        for i, pfn in enumerate(fns, start=1):
            ps += "Patch%04d: %s\n" % (i, pfn)
            if apply_method == 'rpm':
                pa += "%%patch%04d -p1\n" % i
        # PatchXXX: lines after Source0 / #patches_base=
        self._txt, n = re.subn(
            self.RE_AFTER_MAGIC_COMMENTS,
            r'\g<1>%s\n' % ps, self.txt, count=1)

        if n != 1:
            m = None
            for m in re.finditer(self.RE_AFTER_SOURCES, self.txt):
                pass
            if not m:
                raise exception.SpecFileParseError(
                    spec_fn=self.fn,
                    error="Failed to append PatchXXXX: lines")
            i = m.end()
            startnl, endnl = '', ''
            if self._txt[i - 2] != '\n':
                startnl += '\n'
            if self._txt[i] != '\n':
                endnl += '\n'
            self._txt = self._txt[:i] + startnl + ps + endnl + self._txt[i:]
        # %patchXXX -p1 lines after "%setup" if needed
        if apply_method == 'rpm':
            self._txt, n = re.subn(
                r'((?:^|\n)%setup[^\n]*\n)\s*',
                r'\g<1>\n%s\n' % pa, self.txt)
            if n == 0:
                raise exception.SpecFileParseError(
                    spec_fn=self.fn,
                    error="Failed to append %patchXXXX lines after %setup")

    def get_release_parts(self):
        release = self.get_tag('Release')
        return release_parts(release)

    def recognized_release(self):
        """
        Check if this Release value is something we can parse.
        :rtype: bool
        """
        _, _, rest = self.get_release_parts()
        # If "rest" is not a well-known value here, then this package is
        # using a Release value pattern we cannot recognize.
        if rest == '' or re.match(r'%{\??dist}', rest):
            return True
        return False

    def set_macro(self, macro, value):
        if not RPM_AVAILABLE:
            raise exception.RpmModuleNotAvailable()
        rex = self.RE_MACRO_BASE.format(re.escape(macro))
        rpm.delMacro(macro)
        if value:
            # replace
            self._txt, n = re.subn(r'^(%s).*$' % rex, r'\g<1>%s' % value,
                                   self.txt, flags=re.M)
            if n < 1:
                # create new
                self._txt = u'%global {0} {1}\n{2}'.format(
                    macro, value, self.txt)
            rpm.addMacro(macro, value)
        else:
            # remove
            self._txt = re.sub(r'(^|\n)%s[^\n]+\n?' % rex, r'\g<1>', self.txt)

    def get_macro(self, macro, expanded=False):
        if expanded:
            # XXX: rpm module remembers old values even after .spec change
            # and new Spec() instance (that's why this isn't default)
            return self.expand_macro('%{?' + macro + '}')
        else:
            rex = self.RE_MACRO_BASE.format(re.escape(macro))
            m = re.search('^%s(.*)$' % rex, self.txt, flags=re.M)
            if m:
                v = m.group(1).strip(' \t"')
                return v
            return None

    def set_milestone(self, new_milestone):
        self.set_macro('milestone', new_milestone)

    def get_milestone(self):
        ms = self.get_macro('milestone')
        if ms == '%{?milestone}':
            # counter milestone bug from past rdopkg versions :(
            ms = ''
        return ms

    def set_release(self, new_release, milestone=None, postfix=None):
        release = new_release
        if milestone:
            release += '%{?milestone}'
        self.set_milestone(milestone)
        if postfix is None:
            _, _, postfix = self.get_release_parts()
        release += postfix
        if not re.search(r'%{\??dist}', release):
            release += '%{?dist}'

        return self.set_tag('Release', release)

    def bump_release(self, milestone=None, index=None):
        if index == '0':
            # no bumping
            return
        if not milestone:
            milestone = self.get_milestone()
        numbers, _milestone, postfix = self.get_release_parts()
        if index:
            # case insensitive MAJOR/minor/Patch
            index = index.upper()
        if index is None or index == 'LAST-NUMERIC':
            # bump last numeric only Release part by default
            numlist = numbers.split('.')
            i = -1
            if numbers[-1] == '.':
                i = -2
            numlist[i] = str(int(numlist[i]) + 1)
            release = ".".join(numlist)
        else:
            # bump Nth Release part as specified
            if index in RELEASE_PARTS_SEMVER:
                n = RELEASE_PARTS_SEMVER[index]
            else:
                try:
                    n = int(index)
                except ValueError:
                    raise exception.InvalidReleaseBumpIndex(what=index)
                if n < 0:
                    raise exception.InvalidReleaseBumpIndex(
                        what="%s (positive integer required)" % index)
            # index from 1
            i = n - 1
            release = numbers + _milestone
            parts = release.split('.')
            try:
                parts[i] = str(int(parts[i]) + 1)
            except ValueError:
                raise exception.InvalidReleaseBumpIndex(
                    what="%s. part of Release '%s' isn't numeric: %s" % (
                        n, release, parts[i]))
            except IndexError:
                raise exception.InvalidReleaseBumpIndex(
                    what="%s (Release: %s)" % (
                        n, release))
            release = ".".join(parts)
        return self.set_release(release, milestone=milestone, postfix=postfix)

    def get_vr(self, epoch=None):
        """get VR string from .spec Version, Release and Epoch

        epoch is None: prefix epoch if present (default)
        epoch is True: prefix epoch even if not present (0:)
        epoch is False: omit epoch even if present
        """
        version = self.get_tag('Version', expand_macros=True)
        e = None
        if epoch is None or epoch:
            try:
                e = self.get_tag('Epoch')
            except exception.SpecFileParseError:
                pass
        if epoch is None and e:
            epoch = True
        if epoch:
            if not e:
                e = '0'
            version = '%s:%s' % (e, version)
        release = self.get_tag('Release')
        release = re.sub(r'%\{?\??dist\}?$', '', release)
        release = self.expand_macro(release)
        if release:
            return '%s-%s' % (version, release)
        return version

    def get_nvr(self, epoch=None):
        """get NVR string from .spec Name, Version, Release and Epoch"""
        name = self.get_tag('Name', expand_macros=True)
        vr = self.get_vr(epoch=epoch)
        return '%s-%s' % (name, vr)

    def new_changelog_entry(self, user, email, changes=[]):
        changes_str = "\n".join(map(lambda x: "- %s" % x, changes)) + "\n"
        date = time.strftime('%a %b %d %Y')
        # TODO: detect if there is '-' in changelog entries and use it if so
        vr = self.get_vr()
        head = "* %s %s <%s> %s" % (date, user, email, vr)
        entry = "%s\n%s\n" % (head, changes_str)
        self._txt = re.sub(r'(^%changelog\n)', r'\g<1>%s' % entry,
                           self.txt, count=1, flags=re.M)

    def save(self):
        """ Write the textual content (self._txt) to .spec file (self.fn). """
        if not self.txt:
            # no changes
            return
        if not self.fn:
            raise exception.InvalidAction(
                "Can't save .spec file without its file name specified.")
        f = codecs.open(self.fn, 'w', encoding='utf-8')
        f.write(self.txt)
        f.close()
        self._rpmspec = None

    def get_source_urls(self):
        # arcane rpm constants, now in python!
        sources = list(filter(lambda x: x[2] == 1, self.rpmspec.sources))
        if len(sources) == 0:
            error = "No sources found"
            raise exception.SpecFileParseError(spec_fn=self.fn, error=error)
        # OpenStack packages seem to always use only one tarball
        sources0 = list(filter(lambda x: x[1] == 0, sources))
        if len(sources0) == 0:
            error = "Source0 not found"
            raise exception.SpecFileParseError(spec_fn=self.fn, error=error)
        source_url = sources0[0][0]
        return [source_url]

    def get_source_fns(self):
        return list(map(os.path.basename, self.get_source_urls()))

    def get_last_changelog_entry(self, strip=False):
        changelog = ''
        r = re.split("^%changelog\n", self.txt, flags=re.I | re.M)
        if len(r) > 2:
            raise exception.MultipleChangelog()
        if len(r) == 2:
            changelog = r[1].strip()
        entries = re.split(r'\n\n+', changelog)
        entry = entries[0]
        lines = entry.split("\n")
        if strip:
            lines = list(map(lambda x: x.lstrip(" -*\t"), lines))
        return lines[0], lines[1:]

    def get_requires(self, versions_as_string=False, remove_epoch=True,
                     normalize_py23=False):
        reqs = defaultdict(set)
        for pkg in self.rpmspec.packages:
            pkg_reqs = pkg.header.dsFromHeader('requirename')
            for req in pkg_reqs:
                m = re.match(r'R (\S+)\s+([=<>!]+)\s*(\S+)', req.DNEVR())
                if m:
                    name, eq, ver = m.groups()
                    if eq == '=':
                        eq = '=='
                    if remove_epoch:
                        _, sep, rest = ver.partition(':')
                        if sep:
                            ver = rest
                    if normalize_py23:
                        name = re.sub(r'^python[23]-', 'python-', name)
                    reqs[name].add(eq + ' ' + ver)
                else:
                    name = req.N()
                    if normalize_py23:
                        name = re.sub(r'^python[23]-', 'python-', name)
                    reqs[name]
        if versions_as_string:
            for name in reqs:
                reqs[name] = ','.join(reqs[name])
        return reqs
