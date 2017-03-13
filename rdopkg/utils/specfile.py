import codecs
from collections import defaultdict
import os
import re
import time

import exception

RPM_AVAILABLE = False
try:
    import rpm
    import rpmUtils.miscutils
    RPM_AVAILABLE = True
except ImportError:
    pass


def spec_fn(spec_dir='.'):
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
        txt = codecs.open(pfn, 'r', encoding='utf-8').read()
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
    """
    numver, tail = version_parts(version)
    if numver and not re.match('\d', numver):
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
    return s.find('%{') != -1


def nvrcmp(nvr1, nvr2):
    if not RPM_AVAILABLE:
        raise exception.RpmModuleNotAvailable()
    t1 = rpmUtils.miscutils.stringToVersion(nvr1)
    t2 = rpmUtils.miscutils.stringToVersion(nvr2)
    return rpm.labelCompare(t1, t2)


def vcmp(v1, v2):
    if not RPM_AVAILABLE:
        raise exception.RpmModuleNotAvailable()
    t1 = ('0', v1, '')
    t2 = ('0', v2, '')
    return rpm.labelCompare(t1, t2)


def nvr2version(nvr):
    if not RPM_AVAILABLE:
        raise exception.RpmModuleNotAvailable()
    _, v, _, _, _ = rpmUtils.miscutils.splitFilename(nvr)
    return v


class Spec(object):
    """
    Lazy .spec file parser and editor.
    """

    RE_PATCH = r'(?:^|\n)(Patch\d+:)'
    RE_AFTER_SOURCES = r'((?:^|\n)Source\d*:[^\n]*\n\n?)'
    RE_AFTER_PATCHES_BASE = (
        r'((?:^|\n)(?:#[ \t]*\n)*#\s*patches_base\s*=[^\n]*\n(?:#[ '
        r'\t]*\n)*)\n*')
    RE_MACRO_BASE = r'%global\s+{0}\s+'

    def __init__(self, fn=None, txt=None):
        self._fn = fn
        self._txt = txt
        self._rpmspec = None

    @property
    def fn(self):
        if not self._fn:
            self._fn = spec_fn()
        return self._fn

    @property
    def txt(self):
        if not self._txt:
            self._txt = codecs.open(self.fn, 'r', encoding='utf-8').read()
        return self._txt

    @property
    def rpmspec(self):
        if not self._rpmspec:
            if not RPM_AVAILABLE:
                raise exception.RpmModuleNotAvailable()
            rpm.addMacro('_sourcedir',
                         os.path.dirname(os.path.realpath(self.fn)))
            try:
                self._rpmspec = rpm.spec(self.fn)
            except ValueError, e:
                raise exception.SpecFileParseError(spec_fn=self.fn,
                                                   error=e.args[0])
        return self._rpmspec

    def expand_macro(self, macro):
        if not RPM_AVAILABLE:
            raise exception.RpmModuleNotAvailable()
        return rpm.expandMacro(macro)

    def get_tag(self, tag, default=exception.SpecFileParseError,
                expand_macros=False):
        m = re.search('^%s:\s+(\S.*)$' % tag, self.txt, re.M)
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

    def get_patches_base(self, expand_macros=False):
        """Return a tuple (version, number_of_commits) that are parsed
        from the patches_base in the specfile.
        """
        match = re.search(r'(?<=patches_base=)[\w.+?%{}]+', self.txt)
        if not match:
            return None, 0

        patches_base = match.group()
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

        For example a comment as such:
            # patches_ignore=(regex)

        would mean this method returns the string '(regex)'

        Only a very limited subset of characters are accepted so no fancy stuff
        like matching groups etc.
        """
        match = re.search(r'# *patches_ignore=([\w *.+?[\]{,}\-_]+)', self.txt)
        if not match:
            return None
        regex_string = match.group(1)
        try:
            return re.compile(regex_string)
        except:
            return None

    def _create_new_patches_base(self, base):
        self._txt, n = re.subn(
            self.RE_PATCH,
            r'\n#\n# patches_base=%s\n#\n\g<1>' % base,
            self.txt, count=1, flags=re.M)
        if n != 1:
            self._txt, n = re.subn(
                self.RE_AFTER_SOURCES,
                r'\g<1>#\n# patches_base=%s\n#\n\n' % base,
                self.txt, count=1, flags=re.M)
        if n != 1:
            raise exception.SpecFileParseError(
                spec_fn=self.fn,
                error="Unable to create new #patches_base entry.")

    def set_patches_base(self, base):
        v, _ = self.get_patches_base()

        if 'patches_ignore' in self.txt and (base is None or base == ''):
            base = self.get_tag('Version', expand_macros=True)
        if base:
            regex = r'^#\s*patches_base*'
            if v is None and re.search(regex, self.txt, flags=re.M) is None:
                self._create_new_patches_base(base)
            else:
                lines = self.txt.split('\n')
                patch_base_regex = re.compile('(#\s*patches_base\s*=\s*)\w*')
                for idx, line in enumerate(lines):
                    match = patch_base_regex.match(line)
                    if match is not None:
                        out_str = '{0}{1}'.format(match.group(1), base)
                        lines[idx] = out_str
                        break
                else:
                    raise exception.SpecFileParseError(
                        spec_fn=self.fn,
                        error="Unable to set new #patches_base")
                self._txt = '\n'.join(lines)

        else:
            if v is not None:
                # Drop magic comment patches_base and following empty comments
                self._txt = re.sub(
                    r'(?:^#)+\s*patches_base\s*=[^\n]*\n(?:^#\n)*',
                    '', self.txt, flags=re.M)

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

    def sanity_check_buildarch(self):
        # make sure BuildArch is AFTER SourceX and PatchX lines,
        # otherwise %{patches} macro is empty which causes trouble
        bm = re.search('^BuildArch:', self.txt, flags=re.M)
        if not bm:
            return
        bi = bm.start()
        sm = re.search('^Source\d+:', self.txt, flags=re.M)
        if sm:
            si = sm.start()
            if bi < si:
                raise exception.BuildArchSanityCheckFailed()
        pm = re.search('^Patch\d+:', self.txt, flags=re.M)
        if pm:
            pi = pm.start()
            if bi < pi:
                raise exception.BuildArchSanityCheckFailed()

    def sanity_check_patches_base(self):
        # duplicate patches_base might lead to unexpected behavior
        bases = re.findall('^#\s*patches_base', self.txt, flags=re.M)
        if len(bases) > 1:
            raise exception.DuplicatePatchesBaseError()

    def sanity_check(self):
        method = self.patches_apply_method()
        if method in ['git-am', 'autosetup']:
            self.sanity_check_buildarch()
        self.sanity_check_patches_base()

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
            self.RE_AFTER_PATCHES_BASE,
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
        _, _, rest = self.get_release_parts()
        if rest == '' or re.match('%{\??dist}', rest):
            return True
        return False

    def set_macro(self, macro, value):
        if not RPM_AVAILABLE:
            raise exception.RpmModuleNotAvailable()
        rex = self.RE_MACRO_BASE.format(re.escape(macro))
        rpm.delMacro(macro)
        if value:
            # replace
            self._txt, n = re.subn(r'^(%s).*$' % rex, '\g<1>%s' % value,
                                   self.txt, flags=re.M)
            if n < 1:
                # create new
                self._txt = '%global {0} {1}\n{2}'.format(
                    macro, value, self.txt)
            rpm.addMacro(macro, value)
        else:
            # remove
            self._txt = re.sub(r'(^|\n)%s[^\n]+\n?' % rex, '\g<1>', self.txt)

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
        if not release.endswith('%{?dist}'):
            release += '%{?dist}'

        return self.set_tag('Release', release)

    def bump_release(self, milestone=None):
        numbers, _milestone, postfix = self.get_release_parts()
        if not milestone:
            milestone = self.get_milestone()
        numlist = numbers.split('.')
        i = -1
        if numbers[-1] == '.':
            i = -2
        numlist[i] = str(int(numlist[i]) + 1)
        release = ".".join(numlist)
        return self.set_release(release, milestone=milestone, postfix=postfix)

    def get_nvr(self, epoch=None):
        """get NVR string from .spec Version, Release and Epoch

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

    def new_changelog_entry(self, user, email, changes=[]):
        changes_str = "\n".join(map(lambda x: "- %s" % x, changes)) + "\n"
        date = time.strftime('%a %b %d %Y')
        # TODO: detect if there is '-' in changelog entries and use it if so
        nvr = self.get_nvr()
        head = "* %s %s <%s> %s" % (date, user, email, nvr)
        entry = "%s\n%s\n" % (head, changes_str)
        self._txt = re.sub(r'(%changelog\n)', r'\g<1>%s' % entry, self.txt)

    def save(self):
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
        sources = filter(lambda x: x[2] == 1, self.rpmspec.sources)
        if len(sources) == 0:
            error = "No sources found"
            raise exception.SpecFileParseError(spec_fn=self.fn, error=error)
        # OpenStack packages seem to always use only one tarball
        sources0 = filter(lambda x: x[1] == 0, sources)
        if len(sources0) == 0:
            error = "Source0 not found"
            raise exception.SpecFileParseError(spec_fn=self.fn, error=error)
        source_url = sources0[0][0]
        return [source_url]

    def get_source_fns(self):
        return map(os.path.basename, self.get_source_urls())

    def get_last_changelog_entry(self, strip=False):
        _, changelog = self.txt.split("%changelog\n")
        changelog = changelog.strip()
        entries = re.split(r'\n\n+', changelog)
        entry = entries[0]
        lines = entry.split("\n")
        if strip:
            lines = map(lambda x: x.lstrip(" -*\t"), lines)
        return lines[0], lines[1:]

    def get_requires(self, versions_as_string=False, remove_epoch=True):
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
                    reqs[name].add(eq + ' ' + ver)
                else:
                    name = req.N()
                    reqs[name]
        if versions_as_string:
            for name in reqs:
                reqs[name] = ','.join(reqs[name])
        return reqs
