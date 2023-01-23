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


def get_resource_provider_info(compute_client, placement_client):
    # get host aggregates to look up things like az
    nova_aggregates = list(compute_client.aggregates())

    azones = {}
    project_filters = {}
    for agg in nova_aggregates:
        az = agg.metadata.get("availability_zone")
        if az:
            azones[agg.uuid] = az

        projects = []
        for key in agg.metadata.keys():
            if key.startswith("filter_tenant_id"):
                projects.append(agg.metadata[key])
        if projects:
            # TODO(johngarbutt): expose project id to aggregate names?
            project_filters[agg.uuid] = {"name": agg.name, "projects": projects}

    # print(json.dumps(azones, indent=2))
    # print(json.dumps(project_filters, indent=2))

    raw_rps = list(placement_client.resource_providers())

    resource_providers = {}
    for raw_rp in raw_rps:
        rp = {"uuid": raw_rp.id}
        resource_providers[raw_rp.name] = rp
        # TODO - get aggregates
        response = placement_client.get(
            f"/resource_providers/{raw_rp.id}/aggregates",
            headers={"OpenStack-API-Version": "placement 1.19"},
        )
        response.raise_for_status()
        aggs = response.json()
        rp["aggregates"] = aggs["aggregates"]
        for agg_id in rp["aggregates"]:
            if agg_id in azones:
                rp["az"] = azones[agg_id]
            if agg_id in project_filters:
                rp["project_filter"] = project_filters[agg_id]["name"]
    return resource_providers


def print_details(compute_client, placement_client):
    flavors = list(compute_client.flavors())
    capacity_per_flavor = get_capacity_per_flavor(placement_client, flavors)

    # total capacity per flavor
    flavor_names = sorted([f.name for f in flavors])
    for flavor_name in flavor_names:
        counts = capacity_per_flavor.get(flavor_name, {}).values()
        total = 0 if not counts else sum(counts)
        print(f'openstack_total_capacity_per_flavor{{flavor="{flavor_name}"}} {total}')

    # capacity per host
    resource_providers = get_resource_provider_info(compute_client, placement_client)
    hostnames = sorted(resource_providers.keys())
    for hostname in hostnames:
        rp = resource_providers[hostname]
        rp_id = rp["uuid"]
        for flavor_name in flavor_names:
            all_counts = capacity_per_flavor.get(flavor_name, {})
            our_count = all_counts.get(rp_id, 0)
            if our_count == 0:
                continue
            host_str = f'hypervisor="{hostname}"'
            az = rp.get("az")
            if az:
                host_str += f',az="{az}"'
            project_filter = rp.get("project_filter")
            if project_filter:
                host_str += f',project_filter="{project_filter}"'
            print(
                f'openstack_capacity_by_hostname{{{host_str},flavor="{flavor_name}"}} {our_count}'
            )


def print_exporter_data(app):
    print_details(app.compute_client, app.placement_client)


if __name__ == "__main__":
    conn = openstack.connect()
    print_details(conn.compute, conn.placement)