#!/usr/bin/env python3

import collections
import json

import openstack


def get_capacity_per_flavor(placement_client, flavors):
    capacity_per_flavor = {}

    for flavor in flavors:
        resources, traits = get_placement_request(flavor)
        max_per_host = get_max_per_host(placement_client, resources, traits)
        capacity_per_flavor[flavor.name] = max_per_host

    return capacity_per_flavor


def get_placement_request(flavor):
    resources = {"MEMORY_MB": flavor.ram, "DISK_GB": (flavor.disk + flavor.ephemeral)}
    required_traits = []
    for key, value in flavor.extra_specs.items():
        if "trait:" == key[:6]:
            if value == "required":
                required_traits.append(key[6:])
        if "resources:" == key[:10]:
            count = int(value)
            resources[key[10:]] = count
        if "hw:cpu_policy" == key and value == "dedicated":
            resources["PCPU"] = flavor.vcpus
    if "PCPU" not in resources.keys() and "VCPU" not in resources.keys():
        resources["VCPU"] = flavor.vcpus
    return resources, required_traits


def get_max_per_host(placement_client, resources, required_traits):
    resource_str = ",".join(
        [key + ":" + str(value) for key, value in resources.items() if value]
    )
    required_str = ",".join(required_traits)
    # TODO(johngarbut): remove disabled!
    forbidden_str = "COMPUTE_STATUS_DISABLED"

    response = placement_client.get(
        "/allocation_candidates",
        params={"resources": resource_str, "required": required_str},
        headers={"OpenStack-API-Version": "placement 1.29"},
    )
    raw_data = response.json()
    count_per_rp = {}
    for rp_uuid, summary in raw_data.get("provider_summaries", {}).items():
        # per resource, get max possible number of instances
        max_counts = []
        for resource, amounts in summary["resources"].items():
            requested = resources.get(resource, 0)
            if requested:
                free = amounts["capacity"] - amounts["used"]
                amount = int(free / requested)
                max_counts.append(amount)
        # available count is the min of the max counts
        if max_counts:
            count_per_rp[rp_uuid] = min(max_counts)

    return count_per_rp


def print_exporter_data(app):
    flavors = list(app.compute_client.flavors())
    capacity_per_flavor = get_capacity_per_flavor(app.placement_client, flavors)

    # total capacity per flavor
    flavor_names = sorted([f.name for f in flavors])
    for flavor_name in flavor_names:
        counts = capacity_per_flavor.get(flavor_name, {}).values()
        total = 0 if not counts else sum(counts)
        print(f'openstack_total_capacity_per_flavor{{flavor="{flavor_name}"}} {total}')

    # capacity per host
    raw_rps = list(app.placement_client.resource_providers())
    resource_providers = {rp.name: rp.id for rp in raw_rps}
    hostnames = sorted(resource_providers.keys())
    for hostname in hostnames:
        rp_id = resource_providers[hostname]
        for flavor_name in flavor_names:
            all_counts = capacity_per_flavor.get(flavor_name, {})
            our_count = all_counts.get(rp_id, 0)
            if our_count == 0:
                continue
            print(
                f'openstack_capacity_by_hostname{{hypervisor="{hostname}",flavor="{flavor_name}"}} {our_count}'
            )
