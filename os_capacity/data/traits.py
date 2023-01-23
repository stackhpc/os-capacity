#!/usr/bin/env python3

import openstack


def get_capacity(conn):
    capacity = {}
    flavors = list(conn.compute.flavors())
    for flavor in flavors:
        resources, traits = get_placement_request(flavor)
        candidates, total = get_candidates(conn, resources, traits, flavor.name)
    return capacity


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

def get_candidates(conn, resources, traits, flavor_name):
    resource_str = ",".join(
        [key + ":" + str(value) for key, value in resources.items() if value]
    )
    print(resource_str)
    return [], 0

def main():
    conn = openstack.connect()
    capacity = get_capacity(conn)
    print(capacity)


main()
