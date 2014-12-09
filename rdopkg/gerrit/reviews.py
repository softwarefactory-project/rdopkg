# Copyright (c) 2013 python-gerrit Developers.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json
import ssh
import filters


class Query(ssh.Client):

    def __init__(self, *args, **kwargs):
        super(Query, self).__init__(*args, **kwargs)
        self._filters = filters.Items()

    def __iter__(self):
        return iter(self._execute())

    def _execute(self):
        """Executes the query and yields items."""

        query = [
            'gerrit', 'query',
            '--current-patch-set',
            str(self._filters),
            '--format=JSON']

        results = self.client.exec_command(' '.join(query))
        stdin, stdout, stderr = results

        for line in stdout:
            normalized = json.loads(line)

            # Do not return the last item
            # since it is the summary of
            # of the query
            if "rowCount" in normalized:
                raise StopIteration

            yield normalized

    def filter(self, *filters):
        """Adds generic filters to use in the query

        For example:

            - is:open
            - is:
        :param filters: List or tuple of projects
        to add to the filters.
        """
        self._filters.extend(filters)
        return self


class Review(ssh.Client):
    """Single review instance.

    This can be used to approve, block or modify
    a review.

    :params review: The commit sha or review,patch-set
    to review.
    """
    def __init__(self, review, *args, **kwargs):
        super(Review, self).__init__(*args, **kwargs)
        self._review = review
        self._status = None
        self._verified = None
        self._code_review = None

    def verify(self, value):
        """The verification score for this review."""
        self._verified = value

    def review(self, value):
        """The score for this review."""
        self._code_review = value

    def status(self, value):
        """Sets the status of this review

        Available options are:
            - restore
            - abandon
            - workinprogress
            - readyforreview
        """
        self._status = value

    def commit(self, message=None):
        """Executes the command

        :params message: The message
        to use as a comment for this
        action.
        """

        flags = filters.Items()

        if self._status:
            flags.add_flags(self._status)

        if self._code_review is not None:
            flags.add_flags("code-review %s" % self._code_review)

        if self._verified is not None:
            flags.add_flags("verified %s" % self._verified)

        if message:
            flags.add_flags("message '%s'" % message)

        query = ['gerrit', 'review', str(flags), str(self._review)]

        results = self.client.exec_command(' '.join(query))
        stdin, stdout, stderr = results

        # NOTE(flaper87): Log error messages
        error = []
        for line in stderr:
            error.append(line)

        # True if success
        return not error
