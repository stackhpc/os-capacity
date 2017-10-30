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
from os_capacity.data import metrics
from os_capacity.data import resource_provider
from os_capacity.data import server as server_data
from os_capacity.data import users


def get_flavors(app):
    app.LOG.debug("Getting flavors")
    return flavors.get_all(app.compute_client, include_extra_specs=True)


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
        custom_rc = None
        for extra_spec in flavor.extra_specs:
            if extra_spec.startswith('resources:CUSTOM'):
                custom_rc = extra_spec.replace('resources:', '')
                break  # Assuming a good Ironic setup here

        key = (flavor.vcpus, flavor.ram_mb, flavor.disk_gb, custom_rc)
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
        custom_rc = None
        for inventory in inventories:
            if "VCPU" in inventory.resource_class:
                vcpus += inventory.total
            if "MEMORY" in inventory.resource_class:
                ram_mb += inventory.total
            if "DISK" in inventory.resource_class:
                disk_gb += inventory.total
            if inventory.resource_class.startswith('CUSTOM_'):
                custom_rc = inventory.resource_class  # Ironic specific
        key = (vcpus, ram_mb, disk_gb, custom_rc)

        inventory_counts[key] += 1

        allocations = resource_provider.get_allocations(
            app.placement_client, rp)
        if allocations:
            allocation_counts[key] += 1

    for key, inventory_count in inventory_counts.items():
        resources = "VCPU:%s,MEMORY_MB:%s,DISK_GB:%s,%s" % key
        matching_flavors = grouped_flavors[key]
        matching_flavors.sort()
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


def group_usage(app, group_by="user"):
    all_allocations = get_allocations_with_server_info(app, flat_usage=False)

    def get_key(allocation):
        if group_by == "user":
            return allocation.user_id
        if group_by == "project":
            return allocation.project_id
        return "(All)"

    grouped_allocations = collections.defaultdict(list)
    for allocation in all_allocations:
        grouped_allocations[get_key(allocation)].append(allocation)

    all_users = users.get_all(app.identity_client)

    metrics_to_send = []
    summary_tuples = []
    for key, group in grouped_allocations.items():
        grouped_usage = collections.defaultdict(int)
        grouped_usage_days = collections.defaultdict(int)
        for allocation in group:
            for rca in allocation.usage:
                grouped_usage[rca.resource_class] += rca.amount
                if allocation.days < 1:
                    grouped_usage_days[rca.resource_class] += rca.amount
                else:
                    grouped_usage_days[rca.resource_class] += (
                        rca.amount * allocation.days)
            grouped_usage["Count"] += 1
            grouped_usage_days["Count"] += allocation.days or 1

        usage_amounts = ["%s:%s" % (resource_class, total)
                         for resource_class, total in grouped_usage.items()]
        usage_amounts.sort()
        usage = ", ".join(usage_amounts)

        usage_days_amounts = [
            "%s:%s" % (resource_class, total)
            for resource_class, total in grouped_usage_days.items()]
        usage_days_amounts.sort()
        usage_days = ", ".join(usage_days_amounts)

        summary_tuples.append((key, usage, usage_days))

        if group_by == "user":
            dimensions = {"user_id": key}
            if key in all_users:
                dimensions["username"] = all_users.get(key)

            metrics_to_send.append(metrics.Metric(
                name="usage.count",
                value=grouped_usage['Count'],
                dimensions=dimensions))
            metrics_to_send.append(metrics.Metric(
                name="usage.days.count",
                value=grouped_usage_days['Count'],
                dimensions=dimensions))

    # Sort my largest current usage first
    summary_tuples.sort(key=lambda x: x[1], reverse=True)

    if metrics_to_send:
        metrics.send_metrics(app.monitoring_client, metrics_to_send)

    return summary_tuples
