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


Flavor = collections.namedtuple(
    "Flavor", ("id", "name", "vcpus", "ram_mb", "disk_gb", "extra_specs"))


def get_all(compute_client, include_extra_specs=True):
    response = compute_client.get('/flavors/detail').json()
    raw_flavors = response['flavors']
    if include_extra_specs:
        for flavor in raw_flavors:
            url = '/flavors/%s/os-extra_specs' % flavor['id']
            response = compute_client.get(url).json()
            flavor['extra_specs'] = response['extra_specs']
    return [Flavor(f['id'], f['name'], f['vcpus'], f['ram'],
                   (f['disk'] + f['OS-FLV-EXT-DATA:ephemeral']),
                   f.get('extra_specs'))
            for f in raw_flavors]
