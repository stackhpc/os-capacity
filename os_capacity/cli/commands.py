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


import logging

from cliff.lister import Lister

from os_capacity import utils


class CapacityGet(Lister):
    """Show a list of files in the current directory.

    The file name and size are printed by default.
    """

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        capacity = utils.get_capacity()
        return (
            ('Flavor', 'Count'),
            ((entry["flavor"], entry["count"]) for entry in capacity)
        )


class FlavorList(Lister):
    """List all the flavors."""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        flavors = utils.get_flavors(self.app)
        return (('UUID', 'Name', 'VCPUs', 'RAM MB', 'DISK GB'), flavors)


class ListResourcesAll(Lister):
    """List all cloud resources."""

    def take_action(self, parsed_args):
        inventories = utils.get_all_inventories_and_usage(self.app)
        return (('UUID', 'Name', 'VCPU', 'RAM MB', 'DISK GB', 'In Use'),
                inventories)


class ListResourcesGroups(Lister):
    """Lists counts of resource providers with similar inventories."""

    def take_action(self, parsed_args):
        flavors = utils.get_flavors(self.app)
        inventories_and_usage = utils.get_all_inventories_and_usage(self.app)
        groups = utils.group_all_inventories(inventories_and_usage, flavors)
        return (
            ('Resource Class Groups', 'Total', 'Used', 'Free', 'Flavors'),
            groups)


class ListUsagesAll(Lister):
    """List all current resource usages."""

    def take_action(self, parsed_args):
        allocations = utils.get_allocation_list(self.app)
        return (
            ('Provider Name', 'Server UUID', 'Resources',
             'Flavor', 'Days', 'Project', 'User'), allocations)
