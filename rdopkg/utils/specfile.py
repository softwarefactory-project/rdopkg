import codecs
from collections import defaultdict
import os
import re
import time

RPM_AVAILABLE = False
try:
    import rpm
    import rpmUtils.miscutils
    RPM_AVAILABLE = True
except ImportError:
    pass

import exception


def spec_fn(spec_dir='.'):
    specs = [f for f in os.listdir(spec_dir) \
             if os.path.isfile(f) and f.endswith('.spec')]
    if not specs:
        raise exception.SpecFileNotFound()
    if len(specs) != 1:
        raise exception.MultipleSpecFilesFound()
    return specs[0]


def version_parts(version):
    """
    Split a version into numeric and non-numeric (milestone) parts if possible.
    """
    m = re.match('(\d[\d.]*)(?:\.(.+))?$', version)
    if m:
        return m.groups()
    return version, None


def release_parts(release):
    """
    Split a release string into numeric, milestone and macro parts.
    """
    m = re.match('([\d.]*)([^%{}]*)(.*)$', release)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return '', '', release


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
    RE_AFTER_SOURCES = r'((?:^|\n)Source\d+:[^\n]*\n\n)'
    RE_AFTER_PATCHES_BASE = (
        r'((?:^|\n)(?:#\n)*#\s*patches_base\s*=[^\n]*\n(?:#\n)*)\n*')

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
        rs = self.rpmspec
        return rpm.expandMacro(macro)

    def get_tag(self, tag, expand_macros=False):
        m = re.search('^%s:\s+(\S.*)$' % tag, self.txt, re.M)
        if not m:
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
        except ValueError as e:
            n_commits = 0
        return patches_base_ref, n_commits

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
        if base:
            if v is None:
                self._create_new_patches_base(base)
            else:
                self._txt, n = re.subn(
                    r'(#\s*patches_base\s*=\s*)[\w.+]*',
                    r'\g<1>%s' % base, self.txt, flags=re.M)
                if n != 1:
                    raise exception.SpecFileParseError(
                        spec_fn=self.fn,
                        error="Unable to set new #patches_base")
        else:
            if v is not None:
                self._txt = re.sub(
                    r'(?:\n#)+\s*patches_base\s*=[^\n]*\n(?:#\n)*',
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
        for m in re.finditer(r'^\s*Patch\d+:\s*(\S+)\s*$', self.txt, flags=re.M):
            fns.append(m.group(1))
        return fns

    def wipe_patches(self):
        self._txt = re.sub(r'\n+(?:(?:Patch|.patch)\d+[^\n]*)', '', self.txt)

    def buildarch_sanity_check(self):
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

    def sanity_check(self):
        if self.patches_apply_method() == 'git-am':
            self.buildarch_sanity_check()

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
        ## PatchXXX: lines after Source0 / #patches_base=
        self._txt, n = re.subn(
            self.RE_AFTER_PATCHES_BASE,
            r'\g<1>%s\n' % ps, self.txt, count=1)
        if n != 1:
            self._txt, n = re.subn(
                self.RE_AFTER_SOURCES,
                r'\g<1>%s\n' % ps, self.txt, count=1)
        if n != 1:
            raise exception.SpecFileParseError(
                spec_fn=self.fn,
                error="Failed to append PatchXXXX: lines")
        ## %patchXXX -p1 lines after "%setup" if needed
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

    def set_release(self, new_release, milestone=None, postfix=None):
        recognized_format = True
        release = new_release
        if milestone:
            release += '.%s' % milestone
        if postfix is None:
            _, _, postfix = self.get_release_parts()
        release += postfix
        return self.set_tag('Release', release)

    def bump_release(self, milestone=None):
        numbers, milestone, postfix = self.get_release_parts()
        numlist = numbers.split('.')
        i = -1
        if numbers[-1] == '.':
            i = -2
        numlist[i] = str(int(numlist[i]) + 1)
        release = ".".join(numlist)
        return self.set_release(release, milestone=milestone, postfix=postfix)

    def new_changelog_entry(self, user, email, changes=[]):
        changes_str = "\n".join(map(lambda x: "- %s" % x, changes)) + "\n"
        date = time.strftime('%a %b %d %Y')
        version = self.get_tag('Version', expand_macros=True)
        try:
            epoch = self.get_tag('Epoch')
            version = '%s:%s' % (epoch, version)
        except exception.SpecFileParseError:
            pass
        release = self.get_tag('Release', expand_macros=True)
        # Assume release ends with %{?dist}
        release, _, _ = release.rpartition('.')
        # TODO: detect if there is '-' in changelog entries and use it if so
        head = "* %s %s <%s> %s-%s" % (date, user, email, version, release)
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
                    reqs[name].add(eq + ver)
                else:
                    name = req.N()
                    reqs[name]
        if versions_as_string:
            for name in reqs:
                reqs[name] = ','.join(reqs[name])
        return reqs
