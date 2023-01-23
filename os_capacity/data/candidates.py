#!/usr/bin/env python3

import openstack


def get_capacity(conn):
    flavors = list(conn.compute.flavors())
    print("Flavor count: " + str(len(flavors)))

    capacity_per_flavor = {}
    for flavor in flavors:
        resources, traits = get_placement_request(flavor)
        candidates = get_candidates(conn, resources, traits, flavor.name)
        # intentionally add empty responses into this
        capacity_per_flavor[flavor.name] = candidates
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
    if "PCPU" not in resources.keys() and "VCPU" not in resources.keys():
        resources["VCPU"] = flavor.vcpus
    return resources, required_traits


def get_candidates(conn, resources, required_traits, flavor_name):
    resource_str = ",".join(
        [key + ":" + str(value) for key, value in resources.items() if value]
    )
    required_str = ",".join(required_traits)
    # TODO(johngarbut): remove disabled!
    forbidden_str = "COMPUTE_STATUS_DISABLED"

    response = conn.placement.get(
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

    print("Found " + str(len(count_per_rp.keys())) + " candidate hosts for " + flavor_name)
    return count_per_rp


def main():
    conn = openstack.connect()
    capacity_per_flavor = get_capacity(conn)
    import json
    print(json.dumps(capacity_per_flavor, indent=2))


main()
