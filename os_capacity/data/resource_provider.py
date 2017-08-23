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


ResourceProvider = collections.namedtuple(
    "ResourceProvider", ("uuid", "name"))

Inventory = collections.namedtuple(
    "Inventory", ("resource_provider_uuid", "resource_class", "total"))

Allocation = collections.namedtuple(
    "Allocation", ("resource_provider_uuid", "consumer_uuid",
                   "resources"))

ResourceClassAmount = collections.namedtuple(
    "ResourceClassAmount", ("resource_class", "amount"))


def get_all(placement_client):
    response = placement_client.get("/resource_providers").json()
    raw_rps = response['resource_providers']
    return [ResourceProvider(f['uuid'], f['name']) for f in raw_rps]


def get_inventories(placement_client, resource_provider):
    uuid = resource_provider.uuid
    url = "/resource_providers/%s/inventories" % uuid
    response = placement_client.get(url).json()
    raw_inventories = response['inventories']

    inventories = []
    for resource_class, raw_inventory in raw_inventories.items():
        inventory = Inventory(
            uuid, resource_class, raw_inventory['total'])
        inventories.append(inventory)

    return inventories


def get_all_inventories(placement_client, resource_providers=None):
    if resource_providers is None:
        resource_providers = get_all(placement_client)

    inventories = []
    for resource_provider in resource_providers:
        inventories += get_inventories(placement_client, resource_provider)

    return inventories


def get_allocations(placement_client, resource_provider):
    allocations = []
    url = "/resource_providers/%s/allocations" % resource_provider.uuid
    response = placement_client.get(url).json()
    raw_allocations = response['allocations']
    for consumer_uuid, raw_allocation in raw_allocations.items():
        raw_resources = raw_allocation['resources']
        resources = []
        for resource_class, amount in raw_resources.items():
            resources.append(ResourceClassAmount(resource_class, amount))
        resources.sort()

        allocations.append(Allocation(
            resource_provider.uuid, consumer_uuid, resources))
    return allocations


def get_all_allocations(placement_client, resource_providers=None):
    if resource_providers is None:
        resource_providers = get_all(placement_client)

    allocations = []
    for resource_provider in resource_providers:
        allocations += get_allocations(placement_client, resource_provider)

    return allocations
