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


def get_providers_with_resources_and_servers(app):
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


def group_providers_by_type_with_capacity(app):
    # TODO(johngarbutt) this flavor grouping is very ironic specific
    all_flavors = flavors.get_all(app.compute_client)
    grouped_flavors = collections.defaultdict(list)
    for flavor in all_flavors:
        key = (flavor.vcpus, flavor.ram_mb, flavor.disk_gb)
        grouped_flavors[key] += [flavor.name]

    all_resource_providers = resource_provider.get_all(app.placement_client)

    inventory_counts = collections.defaultdict(int)
    allocation_counts = collections.defaultdict(int)
    for rp in all_resource_providers:
        inventories = resource_provider.get_inventories(
            app.placement_client, rp)

        # TODO(johngarbutt) much refinement needed to be general...
        vcpus = 0
        ram_mb = 0
        disk_gb = 0
        for inventory in inventories:
            if "VCPU" in inventory.resource_class:
                vcpus += inventory.total
            if "MEMORY" in inventory.resource_class:
                ram_mb += inventory.total
            if "DISK" in inventory.resource_class:
                disk_gb += inventory.total
        key = (vcpus, ram_mb, disk_gb)

        inventory_counts[key] += 1

        allocations = resource_provider.get_allocations(
            app.placement_client, rp)
        if allocations:
            allocation_counts[key] += 1

    for key, inventory_count in inventory_counts.items():
        resources = "VCPU:%s,MEMORY_MB:%s,DISK_GB:%s" % key
        matching_flavors = grouped_flavors[key]
        matching_flavors = ", ".join(matching_flavors)
        total = inventory_count
        used = allocation_counts[key]
        free = total - used

        yield (resources, total, used, free, matching_flavors)


def _get_now():
    # To make it easy to mock in tests
    return datetime.now()


AllocationList = collections.namedtuple(
    "AllocationList", ("resource_provider_name", "consumer_uuid",
                       "usage", "flavor_id", "days",
                       "project_id", "user_id"))


def get_allocations_with_server_info(app, flat_usage=True):
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
        usage = allocation.resources
        if flat_usage:
            usage_amounts = ["%s:%s" % (rca.resource_class, rca.amount)
                             for rca in allocation.resources]
            usage_amounts.sort()
            usage = ", ".join(usage_amounts)

        server = server_data.get(app.compute_client, allocation.consumer_uuid)
        delta = now - server.created
        days_running = delta.days

        allocation_tuples.append(AllocationList(
            rp_name, allocation.consumer_uuid, usage,
            server.flavor_id, days_running, server.project_id,
            server.user_id))

    allocation_tuples.sort(key=lambda x: (x.project_id, x.user_id,
                                          x.days * -1, x.flavor_id))

    return allocation_tuples


UsageSummary = collections.namedtuple(
    "UsageSummary", ("resource_provider_name", "consumer_uuid",
                     "usage", "flavor_id", "days",
                     "project_id", "user_id"))


def group_usage(app):
    all_allocations = get_allocations_with_server_info(app, flat_usage=False)

    # TODO(johngarbutt) add a parameter for sort key
    def get_key(allocation):
        return allocation.user_id

    grouped_allocations = collections.defaultdict(list)
    for allocation in all_allocations:
        grouped_allocations[get_key(allocation)].append(allocation)

    summary_tuples = []
    for key, group in grouped_allocations.items():
        grouped_usage = collections.defaultdict(int)
        for allocation in group:
            for rca in allocation.usage:
                grouped_usage[rca.resource_class] += rca.amount

        usage_amounts = ["%s:%s" % (resource_class, total)
                         for resource_class, total in grouped_usage.items()]
        usage_amounts.sort()
        usage = ", ".join(usage_amounts)

        summary_tuples.append((key, usage))

    summary_tuples.sort()

    return summary_tuples
