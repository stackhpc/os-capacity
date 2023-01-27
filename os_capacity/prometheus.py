#!/usr/bin/env python3

import collections
import json

import openstack


def get_capacity_per_flavor(placement_client, flavors):
    capacity_per_flavor = {}

    for flavor in flavors:
        max_per_host = get_max_per_host(placement_client, flavor)
        capacity_per_flavor[flavor.name] = max_per_host

    return capacity_per_flavor


def get_placement_request(flavor):
    resources = {}
    required_traits = []

    def add_defaults(resources, flavor, skip_vcpu=False):
        resources["MEMORY_MB"] = flavor.ram
        resources["DISK_GB"] = flavor.disk + flavor.ephemeral
        if not skip_vcpu:
            resources["VCPU"] = flavor.vcpus

    for key, value in flavor.extra_specs.items():
        if "trait:" == key[:6]:
            if value == "required":
                required_traits.append(key[6:])
        if "resources:" == key[:10]:
            count = int(value)
            resources[key[10:]] = count
        if "hw:cpu_policy" == key and value == "dedicated":
            resources["PCPU"] = flavor.vcpus
            add_defaults(resources, flavor, skip_vcpu=True)

    # if not baremetal and not PCPU
    # we should add the default vcpu ones
    if not resources:
        add_defaults(resources, flavor)

    return resources, required_traits


def get_max_per_host(placement_client, flavor):
    resources, required_traits = get_placement_request(flavor)
    resource_str = ",".join(
        [key + ":" + str(value) for key, value in resources.items() if value]
    )
    required_str = ",".join(required_traits)
    # TODO(johngarbut): remove disabled!
    forbidden_str = "COMPUTE_STATUS_DISABLED"

    params = {"resources": resource_str}
    if not resource_str:
        raise Exception("we must have some resources here!")
    if required_str:
        params["required"] = required_str

    response = placement_client.get(
        "/allocation_candidates",
        params=params,
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
    if not count_per_rp:
        print(f"# WARNING - no candidates hosts for flavor: {flavor.name} {params}")
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
                # TODO(johngarbutt): loosing info here
                if "project_filter" in rp:
                    rp["project_filter"] = "multiple"
                else:
                    rp["project_filter"] = project_filters[agg_id]["name"]

    project_to_aggregate = collections.defaultdict(list)
    for filter_info in project_filters.values():
        name = filter_info["name"]
        for project in filter_info["projects"]:
            project_to_aggregate[project] += [name]

    return resource_providers, project_to_aggregate


def print_host_details(compute_client, placement_client):
    flavors = list(compute_client.flavors())
    capacity_per_flavor = get_capacity_per_flavor(placement_client, flavors)

    # total capacity per flavor
    flavor_names = sorted([f.name for f in flavors])
    for flavor_name in flavor_names:
        counts = capacity_per_flavor.get(flavor_name, {}).values()
        total = 0 if not counts else sum(counts)
        print(f'openstack_free_capacity_by_flavor{{flavor="{flavor_name}"}} {total}')

    # capacity per host
    resource_providers, project_to_aggregate = get_resource_provider_info(
        compute_client, placement_client
    )
    hostnames = sorted(resource_providers.keys())
    for hostname in hostnames:
        rp = resource_providers[hostname]
        rp_id = rp["uuid"]
        free_space_found = False
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
                f'openstack_free_capacity_by_hypervisor{{{host_str},flavor="{flavor_name}"}} {our_count}'
            )
            free_space_found = True
        if not free_space_found:
            print(f"# WARNING - no free spaces found for {hostname}")

    for project, names in project_to_aggregate.items():
        for name in names:
            print(
                f'openstack_project_filter_aggregate{{project_id="{project}",aggregate="{name}"}} 1'
            )


def print_project_usage(indentity_client, placement_client, compute_client):
    projects = {proj.id: dict(name=proj.name) for proj in indentity_client.projects()}
    for project_id in projects.keys():
        # TODO(johngarbutt) On Xena we should do consumer_type=INSTANCE using 1.38!
        response = placement_client.get(
            f"/usages?project_id={project_id}",
            headers={"OpenStack-API-Version": "placement 1.19"},
        )
        response.raise_for_status()
        usages = response.json()
        projects[project_id]["usages"] = usages["usages"]

        response = compute_client.get(
            f"/os-quota-sets/{project_id}",
            headers={"OpenStack-API-Version": "compute 2.20"},
        )
        response.raise_for_status()
        quotas = response.json().get("quota_set", {})
        projects[project_id]["quotas"] = dict(
            CPUS=quotas.get("cores"), MEMORY_MB=quotas.get("ram")
        )

    # print(json.dumps(projects, indent=2))
    for project_id, data in projects.items():
        name = data["name"]
        project_usages = data["usages"]
        for resource, amount in project_usages.items():
            print(
                f'openstack_project_usage{{project_id="{project_id}",'
                f'project_name="{name}",resource="{resource}"}} {amount}'
            )

        if not project_usages:
            # skip projects with zero usage?
            print(f"# WARNING no usage for project: {name} {project_id}")
            continue
        project_quotas = data["quotas"]
        for resource, amount in project_quotas.items():
            print(
                f'openstack_project_quota{{project_id="{project_id}",'
                f'project_name="{name}",resource="{resource}"}} {amount}'
            )


def print_exporter_data(app):
    print_host_free_details(app.compute_client, app.placement_client)


if __name__ == "__main__":
    conn = openstack.connect()
    print_host_details(conn.compute, conn.placement)
    print_project_usage(conn.identity, conn.placement, conn.compute)
