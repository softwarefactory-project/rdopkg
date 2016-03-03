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


class Items(list):
    key = None

    def add_flags(self, *flags):
        """Adds one or more flags to the query.

        For example:
            current-patch-set -> --current-patch-set
        """
        if not isinstance(flags, (list, tuple)):
            flags = [str(flags)]

        self.extend(["--%s" % f for f in flags])
        return self

    def add_items(self, key, value):

        if not isinstance(value, (list, tuple)):
            value = [str(value)]

        self.extend(["%s:%s" % (key, val) for val in value])
        return self

    def __repr__(self):
        subs_repr = [str(i) for i in self]

        base = '(%s)'
        key = self.key

        if not key:
            key, base = ' ', '%s'

        return base % key.join(subs_repr)


class OrFilter(Items):
    key = ' OR '


class AndFilter(Items):
    key = ' AND '
