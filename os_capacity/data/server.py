# Copyright (c) 2017 StackHPC Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import collections
from datetime import datetime


Server = collections.namedtuple(
    "Server", ("uuid", "name", "created",
               "user_id", "project_id", "flavor_id"))


def _parse_created(raw_created):
    """Parse a string like 2017-02-14T19:23:58Z"""
    return datetime.strptime(raw_created, "%Y-%m-%dT%H:%M:%SZ")


def get(compute_client, uuid):
    url = "/servers/%s" % uuid
    raw_server = compute_client.get(url).json()['server']
    return Server(
        uuid=raw_server['id'],
        name=raw_server['name'],
        created=_parse_created(raw_server['created']),
        user_id=raw_server['user_id'],
        project_id=raw_server['tenant_id'],
        flavor_id=raw_server['flavor'].get('id'),
    )
