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

from os_capacity.data import metrics
from os_capacity import utils


class FlavorList(Lister):
    """List all the flavors."""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        flavors = utils.get_flavors(self.app)
        return (('UUID', 'Name', 'VCPUs', 'RAM MB', 'DISK GB'), flavors)


class ListResourcesAll(Lister):
    """List all resource providers, with their resources and servers."""

    def take_action(self, parsed_args):
        inventories = utils.get_providers_with_resources_and_servers(self.app)
        return (('Provider Name', 'Resources', 'Severs'), inventories)


class ListResourcesGroups(Lister):
    """Lists counts of resource providers with similar inventories."""

    def take_action(self, parsed_args):
        groups = utils.group_providers_by_type_with_capacity(self.app) 
        groups = list(groups)  # convert iterator

        metrics_to_send = []
        for group in groups:
            flavors = group[4].replace(", ", "-")
            total = group[1]
            used = group[2]
            free = group[3]
            metrics_to_send.append(metrics.Metric(
                name="resources.total.%s" % flavors,
                value=total))
            metrics_to_send.append(metrics.Metric(
                name="resources.used.%s" % flavors,
                value=used))
            metrics_to_send.append(metrics.Metric(
                name="resources.free.%s" % flavors,
                value=free))
        metrics.send_metrics(self.app.monitoring_client, metrics_to_send)

        return (
            ('Resource Class Groups', 'Total', 'Used', 'Free', 'Flavors'),
            groups)


class ListUsagesAll(Lister):
    """List all current resource usages."""

    def take_action(self, parsed_args):
        allocations = utils.get_allocations_with_server_info(self.app)
        return (
            ('Provider Name', 'Server UUID', 'Resources',
             'Flavor', 'Days', 'Project', 'User'), allocations)


class ListUsagesGroup(Lister):
    """Group usage by specified key (by user or project).

    NOTE: The usage days is not complete as it only takes into
    account any currently active servers. Any previously deleted
    servers are not counted.
    """

    def get_parser(self, prog_name):
        parser = super(ListUsagesGroup, self).get_parser(prog_name)
        parser.add_argument('group_by', nargs='?', default='user',
                            help='Group by user_id or project_id or all',
                            choices=['user', 'project', 'all'])
        return parser

    def take_action(self, parsed_args):
        usages = utils.group_usage(self.app, parsed_args.group_by)
        sort_key_title = parsed_args.group_by.title()
        return ((sort_key_title, 'Current Usage', 'Usage Days'), usages)
