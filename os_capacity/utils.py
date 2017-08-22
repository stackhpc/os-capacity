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


def get_capacity():
    return [{"flavor": "foo", "count": 1}]


def get_flavors(app):
    client = app.compute_client
    response = client.get("/flavors/detail").json()
    raw_flavors = response['flavors']
    return [(f['id'], f['name'], f['vcpus'], f['ram'], f['disk'])
            for f in raw_flavors]


def get_resource_providers(app):
    client = app.placement_client
    response = client.get("/resource_providers").json()
    raw_rps = response['resource_providers']
    return [(f['uuid'], f['name']) for f in raw_rps]


def _get_inventories(app, rps):
    client = app.placement_client
    inventories = {}
    for uuid, name in rps:
        url = "/resource_providers/%s/inventories" % uuid
        response = client.get(url).json()
        raw_inventories = response['inventories']
        inventories[uuid] = {}
        for resource_class in raw_inventories.keys():
            max_unit = raw_inventories[resource_class]['max_unit']
            inventories[uuid][resource_class] = max_unit
    return inventories


def get_all_inventories(app):
    rps = get_resource_providers(app)
    all_inventories = _get_inventories(app, rps)

    for rp_uuid, rp_name in rps:
        rp_inventories = all_inventories[rp_uuid]
        yield (rp_uuid, rp_name,
               rp_inventories.get('VCPU'),
               rp_inventories.get('MEMORY_MB'),
               rp_inventories.get('DISK_GB'))


def group_all_inventories(all_inventories, flavors):
    trimed_inventory = [i[2:] for i in all_inventories]
    counted_inventories = collections.Counter(trimed_inventory)

    # TODO(johngarbutt) this flavor grouping is very ironic specific
    grouped_flavors = collections.defaultdict(list)
    for flavor in flavors:
        name = flavor[1]
        trimed = flavor[2:]
        grouped_flavors[trimed] += [name]

    for group in counted_inventories.keys():
        resources = "VCPU:%s,MEMORY_MB:%s,DISK_GB:%s" % group
        matching_flavors = grouped_flavors[group]
        matching_flavors = ", ".join(matching_flavors)
        yield (resources, counted_inventories[group], matching_flavors)
