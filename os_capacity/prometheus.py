#!/usr/bin/env python3
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
import os
import time
import uuid

import openstack
import prometheus_client as prom_client
from prometheus_client import core as prom_core

RESOURCE_PROVIDER_AGGREGATE_CACHE = {}


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
    if required_str:
        required_str += ","
    required_str += "!COMPUTE_STATUS_DISABLED"

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

    skip_aggregate_lookup = (
        int(os.environ.get("OS_CAPACITY_SKIP_AGGREGATE_LOOKUP", "0")) == 1
    )
    resource_providers = {}
    for raw_rp in raw_rps:
        rp = {"uuid": raw_rp.id}
        resource_providers[raw_rp.name] = rp

        if skip_aggregate_lookup:
            # skip checking every resource provider for their aggregates
            continue

        # TODO(johngarbutt): maybe check if cached aggregate still exists?
        aggregates = RESOURCE_PROVIDER_AGGREGATE_CACHE.get(raw_rp.id)
        if aggregates is None:
            response = placement_client.get(
                f"/resource_providers/{raw_rp.id}/aggregates",
                headers={"OpenStack-API-Version": "placement 1.19"},
            )
            response.raise_for_status()
            aggs = response.json()
            rp["aggregates"] = aggs["aggregates"]
            RESOURCE_PROVIDER_AGGREGATE_CACHE[raw_rp.id] = aggs["aggregates"]
        else:
            rp["aggregates"] = aggregates

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


def get_host_details(compute_client, placement_client):
    flavors = list(compute_client.flavors())
    capacity_per_flavor = get_capacity_per_flavor(placement_client, flavors)

    # total capacity per flavor
    free_by_flavor_total = prom_core.GaugeMetricFamily(
        "openstack_free_capacity_by_flavor_total",
        "Free capacity if you fill the cloud full of each flavor",
        labels=["flavor_name", "public"],
    )

    for flavor in flavors:
        counts = capacity_per_flavor.get(flavor.name, {}).values()
        total = 0 if not counts else sum(counts)
        free_by_flavor_total.add_metric([flavor.name, str(flavor.is_public)], total)

    # capacity per host
    free_by_flavor_hypervisor = prom_core.GaugeMetricFamily(
        "openstack_free_capacity_hypervisor_by_flavor",
        "Free capacity for each hypervisor if you fill "
        "remaining space full of each flavor",
        labels=["hypervisor", "flavor_name", "az_aggregate", "project_aggregate"],
    )
    resource_providers, project_to_aggregate = get_resource_provider_info(
        compute_client, placement_client
    )
    hostnames = sorted(resource_providers.keys())
    for hostname in hostnames:
        rp = resource_providers[hostname]
        rp_id = rp["uuid"]
        free_space_found = False
        for flavor in flavors:
            flavor_name = flavor.name
            all_counts = capacity_per_flavor.get(flavor_name, {})
            our_count = all_counts.get(rp_id, 0)
            if our_count == 0:
                continue
            az = rp.get("az", "")
            project_filter = rp.get("project_filter", "")
            free_by_flavor_hypervisor.add_metric(
                [hostname, flavor_name, az, project_filter], our_count
            )
            free_space_found = True
        if not free_space_found:
            # TODO(johngarbutt) allocation candidates only returns some,
            # not all candidates!
            print(f"# WARNING - no free spaces found for {hostname}")

    project_filter_aggregates = prom_core.GaugeMetricFamily(
        "openstack_project_filter_aggregate",
        "Mapping of project_ids to aggregates in the host free capacity info.",
        labels=["project_id", "aggregate"],
    )
    for project, names in project_to_aggregate.items():
        for name in names:
            project_filter_aggregates.add_metric([project, name], 1)
    return resource_providers, [
        free_by_flavor_total,
        free_by_flavor_hypervisor,
        project_filter_aggregates,
    ]


def get_project_usage(indentity_client, placement_client, compute_client):
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

    project_usage_guage = prom_core.GaugeMetricFamily(
        "openstack_project_usage",
        "Current placement allocations per project.",
        labels=["project_id", "project_name", "placement_resource"],
    )
    project_quota_guage = prom_core.GaugeMetricFamily(
        "openstack_project_quota",
        "Current quota set to limit max resource allocations per project.",
        labels=["project_id", "project_name", "quota_resource"],
    )
    for project_id, data in projects.items():
        name = data["name"]
        project_usages = data["usages"]
        for resource, amount in project_usages.items():
            project_usage_guage.add_metric([project_id, name, resource], amount)

        if not project_usages:
            # skip projects with zero usage?
            print(f"# WARNING no usage for project: {name} {project_id}")
            continue
        project_quotas = data["quotas"]
        for resource, amount in project_quotas.items():
            project_quota_guage.add_metric([project_id, name, resource], amount)
    return [project_usage_guage, project_quota_guage]


def get_host_usage(resource_providers, placement_client):
    usage_guage = prom_core.GaugeMetricFamily(
        "openstack_hypervisor_placement_allocated",
        "Currently allocated resource for each provider in placement.",
        labels=["hypervisor", "resource"],
    )
    capacity_guage = prom_core.GaugeMetricFamily(
        "openstack_hypervisor_placement_allocatable_capacity",
        "The total allocatable resource in the placement inventory.",
        labels=["hypervisor", "resource"],
    )
    for name, data in resource_providers.items():
        rp_id = data["uuid"]
        response = placement_client.get(
            f"/resource_providers/{rp_id}/usages",
            headers={"OpenStack-API-Version": "placement 1.19"},
        )
        response.raise_for_status()
        rp_usages = response.json()["usages"]
        resource_providers[name]["usages"] = rp_usages

        for resource, amount in rp_usages.items():
            usage_guage.add_metric([name, resource], amount)

        response = placement_client.get(
            f"/resource_providers/{rp_id}/inventories",
            headers={"OpenStack-API-Version": "placement 1.19"},
        )
        response.raise_for_status()
        inventories = response.json()["inventories"]
        resource_providers[name]["inventories"] = inventories

        for resource, data in inventories.items():
            amount = int(data["total"] * data["allocation_ratio"]) - data["reserved"]
            capacity_guage.add_metric([name, resource], amount)
    # print(json.dumps(resource_providers, indent=2))
    return [usage_guage, capacity_guage]


class OpenStackCapacityCollector(object):
    def __init__(self):
        self.conn = openstack.connect()
        openstack.enable_logging(debug=False)
        print("got openstack connection")
        # for some reason this makes the logging work?!
        self.conn.compute.flavors()

    def collect(self):
        start_time = time.perf_counter()
        collect_id = uuid.uuid4().hex
        print(f"Collect started {collect_id}")
        guages = []

        skip_project_usage = (
            int(os.environ.get("OS_CAPACITY_SKIP_PROJECT_USAGE", "0")) == 1
        )
        skip_host_usage = int(os.environ.get("OS_CAPACITY_SKIP_HOST_USAGE", "0")) == 1

        conn = openstack.connect()
        openstack.enable_logging(debug=False)
        try:
            resource_providers, host_guages = get_host_details(
                conn.compute, conn.placement
            )
            guages += host_guages

            host_time = time.perf_counter()
            host_duration = host_time - start_time
            print(
                "1 of 3: host flavor capacity complete "
                f"for {collect_id} it took {host_duration} seconds"
            )

            if not skip_project_usage:
                guages += get_project_usage(conn.identity, conn.placement, conn.compute)
                project_time = time.perf_counter()
                project_duration = project_time - host_time
                print(
                    "2 of 3: project usage complete "
                    f"for {collect_id} it took {project_duration} seconds"
                )
            else:
                print("2 of 3: skipping project usage")

            if not skip_host_usage:
                guages += get_host_usage(resource_providers, conn.placement)
                host_usage_time = time.perf_counter()
                host_usage_duration = host_usage_time - project_time
                print(
                    "3 of 3: host usage complete for "
                    f"{collect_id} it took {host_usage_duration} seconds"
                )
            else:
                print("3 of 3: skipping host usage")
        except Exception as e:
            print(f"error {e}")

        end_time = time.perf_counter()
        duration = end_time - start_time
        print(f"Collect complete {collect_id} it took {duration} seconds")
        return guages


def main():
    kwargs = {
        "port": int(os.environ.get("OS_CAPACITY_EXPORTER_PORT", 9000)),
        "addr": os.environ.get("OS_CAPACITY_EXPORTER_LISTEN_ADDRESS", "0.0.0.0"),
    }
    prom_client.start_http_server(**kwargs)

    prom_core.REGISTRY.register(OpenStackCapacityCollector())
    # there must be a better way!
    while True:
        time.sleep(5000)


if __name__ == "__main__":
    main()
