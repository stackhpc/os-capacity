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
from os_capacity.data import server as server_data


def get_flavors(app):
    app.LOG.debug("Getting flavors")
    raw_flavors = flavors.get_all(app.compute_client)
    return [(f.id, f.name, f.vcpus, f.ram_mb, f.disk_gb) for f in raw_flavors]


def _get_resource_providers(app):
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


AllocationList = collections.namedtuple(
    "AllocationList", ("resource_provider_name", "consumer_uuid",
                       "usage", "flavor_id", "days",
                       "project_id", "user_id"))

def get_allocation_list(app):
    """Get allocations, add in server and resource provider details."""
    resource_providers = resource_provider.get_all(app.placement_client)
    rp_dict = {rp.uuid: rp.name for rp in resource_providers}

    all_allocations = resource_provider.get_all_allocations(
        app.placement_client, resource_providers)

    now = _get_now()

    allocation_tuples = []
    for allocation in all_allocations:
        rp_name = rp_dict[allocation.resource_provider_uuid]

        # TODO(johngarbutt) this is too presentation like for here
        usage_amounts = ["%s:%s" % (rca.resource_class, rca.amount)
                         for rca in allocation.resources]
        usage_amounts.sort()
        usage_text = ", ".join(usage_amounts)

        server = server_data.get(app.compute_client, allocation.consumer_uuid)
        delta = now - server.created
        days_running = delta.days

        allocation_tuples.append(AllocationList(
            rp_name, allocation.consumer_uuid, usage_text,
            server.flavor_id, days_running, server.project_id,
            server.user_id))

    allocation_tuples.sort(key=lambda x: (x.project_id, x.user_id,
                                          x.days * -1, x.flavor_id))

    return allocation_tuples


def get_all_inventories_and_usage(app):
    resource_providers = resource_provider.get_all(app.placement_client)

    for rp in resource_providers:
        inventories = resource_provider.get_inventories(
            app.placement_client, rp)
        allocations = resource_provider.get_allocations(
            app.placement_client, rp)

        inventory_texts = ["%s:%s" % (i.resource_class, i.total)
                           for i in inventories]
        inventory_texts.sort()
        inventory_text = ", ".join(inventory_texts)

        allocation_texts = [a.consumer_uuid for a in allocations]
        allocation_texts.sort()
        allocation_text = ", ".join(allocation_texts)

        yield (rp.name, inventory_text, allocation_text)


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
