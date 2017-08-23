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

from os_capacity.data import flavors
from os_capacity.data import resource_provider


def get_flavors(app):
    app.LOG.debug("Getting flavors")
    raw_flavors = flavors.get_all(app.compute_client)
    return [(f.id, f.name, f.vcpus, f.ram_mb, f.disk_gb) for f in raw_flavors]


def get_resource_providers(app):
    app.LOG.debug("Getting resource providers")
    raw_rps = resource_provider.get_all(app.placement_client)
    return [(rp.uuid, rp.name) for rp in raw_rps]


def _get_inventories(app, rps):
    app.LOG.debug("Getting all inventories")
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


def _get_now():
    # To make it easy to mock in tests
    return datetime.now()


def _get_server(app, uuid):
    client = app.compute_client
    url = "/servers/%s" % uuid
    raw_server = client.get(url).json()['server']
    return {
        "uuid": raw_server['id'],
        "name": raw_server['name'],
        "created": datetime.strptime(
            raw_server['created'], "%Y-%m-%dT%H:%M:%SZ"),
        "user_id": raw_server['user_id'],
        "project_id": raw_server['tenant_id'],
        "project_id": raw_server['tenant_id'],
        "flavor_id": raw_server['flavor'].get('id'),
    }


def _get_allocations(app, rps):
    app.LOG.debug("Getting all allocations")
    client = app.placement_client
    allocations_by_rp = {}
    for uuid, name in rps:
        url = "/resource_providers/%s/allocations" % uuid
        response = client.get(url).json()
        raw_allocations = response['allocations']
        allocations_by_rp[uuid] = raw_allocations
    return allocations_by_rp


def get_allocation_list(app):
    rps = get_resource_providers(app)
    all_allocations = _get_allocations(app, rps)
    rp_dict = {uuid: name for uuid, name in rps}
    now = _get_now()

    allocation_list = []
    for rp_uuid in all_allocations.keys():
        for server_uuid in all_allocations[rp_uuid].keys():
            rp_name = rp_dict[rp_uuid]
            usage_amounts = all_allocations[rp_uuid][server_uuid]['resources']
            usage_amounts = ["%s:%s" % i for i in usage_amounts.items()]
            usage_amounts.sort()
            usage_text = ", ".join(usage_amounts)

            server = _get_server(app, server_uuid)
            user = server['user_id']
            project = server['project_id']
            created = server['created']
            flavor = server['flavor_id']
            delta = now - created
            days_running = delta.days

            allocation_list.append((
                rp_name, server_uuid, usage_text,
                flavor, days_running, project, user))

    # Order by project, then user, then most days, then flavor
    allocation_list.sort(key=lambda x: (x[5], x[6], x[4] * -1, x[3]))

    return allocation_list


def get_all_inventories_and_usage(app):
    rps = get_resource_providers(app)
    all_inventories = _get_inventories(app, rps)
    all_allocations = _get_allocations(app, rps)

    for rp_uuid, rp_name in rps:
        rp_inventories = all_inventories[rp_uuid]
        has_allocations = True if all_allocations.get(rp_uuid) else False
        yield (rp_uuid, rp_name,
               rp_inventories.get('VCPU'),
               rp_inventories.get('MEMORY_MB'),
               rp_inventories.get('DISK_GB'),
               has_allocations)


def group_all_inventories(all_inventories_and_usage, flavors):
    counted_inventories = collections.defaultdict(int)
    usage = collections.defaultdict(int)
    for inventory in all_inventories_and_usage:
        resource_key = inventory[2:-1]  # TODO(johngarbutt) fix this rubbish
        is_used = inventory[-1]
        counted_inventories[resource_key] += 1
        if is_used:
            usage[resource_key] += 1

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
        total = counted_inventories[group]
        used = usage[group]
        free = total - used

        yield (resources, total, used, free, matching_flavors)
