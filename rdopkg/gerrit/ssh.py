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

import os

import paramiko


class Client(object):

    def __init__(self, host, port=29418, user=None,
                 key=None, config="~/.ssh/config"):

        self.key = key
        self.host = host
        self.port = port
        self.user = user

        config = os.path.expanduser(config)
        if os.path.exists(config):
            ssh = paramiko.SSHConfig()
            ssh.parse(open(config))
            conf = ssh.lookup(host)

            self.host = conf['hostname']
            self.port = int(conf.get('port', self.port))
            self.user = conf.get('user', self.user)
            self.key = conf.get('identityfile', self.key)

    @property
    def client(self):
        if not hasattr(self, "_client"):
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._client.load_system_host_keys()
            self._client.connect(self.host,
                                 port=self.port,
                                 username=self.user,
                                 key_filename=self.key)
        return self._client
