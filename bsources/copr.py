from bs4 import BeautifulSoup
import calendar
import datetime
import os
import re
import urllib

from rdoupdate.bsource import BuildSource
from rdoupdate.errpass import ErrorBool
from rdoupdate.exception import BuildNotAvailable
from rdoupdate.helpers import download_file
from rdoupdate.utils.cmd import run


class HttpListingSource(object):
    def _get_listed_files(self, url, with_time=False):
        page = urllib.urlopen(url).read()
        if re.search('404 (- )?Not Found', page):
            return ErrorBool(err='404 - Not Found')
        soup = BeautifulSoup(page)
        files = []
        for tr in soup.find_all('tr'):
            aaa = tr.select('td a')
            if not aaa:
                continue
            a = aaa[0]
            href = a.get('href')
            if not href.endswith('.rpm'):
                continue
            t = None
            for td in tr.find_all('td'):
                try:
                    # lighttpd
                    t = datetime.datetime.strptime(td.text, '%Y-%b-%d %H:%M:%S')
                    break
                except Exception:
                    pass
                try:
                    # apache
                    t = datetime.datetime.strptime(td.text, '%Y-%b-%d %H:%M')
                    break
                except Exception:
                    pass
            files.append((href, t))
        if not files:
            return ErrorBool(err='No rpms found in build directory.')
        return files

    def _download_build_http(self, url):
        rpms = self._get_listed_files(url)
        if not rpms:
            return rpms
        for rpm, time in rpms:
            purl = "%s/%s" % (url, rpm)
            download_file(purl)
            if time:
                # preserve times if possible
                stamp = calendar.timegm(time.timetuple())
                os.utime(rpm, (stamp, stamp))
        return ErrorBool()

    def _build_available_http(self, url):
        rpms = self._get_listed_files(url)
        if rpms:
            return ErrorBool()
        else:
            return rpms


class CoprJruzickaSource(BuildSource, HttpListingSource):
    name = 'copr-jruzicka'
    copr_user = 'jruzicka'
    copr_base_url = 'http://copr-be.cloud.fedoraproject.org/results'

    def _copr_repo_url(self, build):
        url = '{base}/{user}/rdo-{repo}-{dist}/{dist}-x86_64/{id}'.format(
            base=self.copr_base_url, user=self.copr_user,
            repo=build.repo, dist=build.dist, id=build.id)
        return url

    def _download_build(self, build):
        url = self._copr_repo_url(build)
        r = self._download_build_http(url)
        if not r:
            raise BuildNotAvailable(build_id=build.id, source=build.source,
                                    detail=r.err)

    def _build_available(self, build):
        url = self._copr_repo_url(build)
        return self._build_available_http(url)

