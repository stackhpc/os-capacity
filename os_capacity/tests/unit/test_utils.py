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

import datetime
import mock
import unittest

from os_capacity.data import flavors
from os_capacity.data import resource_provider
from os_capacity.data import server
from os_capacity import utils


class TestUtils(unittest.TestCase):

    @mock.patch.object(flavors, "get_all")
    def test_get_flavors(self, mock_flavors):
        mock_flavors.return_value = [flavors.Flavor(
            id="id", name="name", vcpus=1, ram_mb=2, disk_gb=3)]
        app = mock.Mock()

        result = utils.get_flavors(app)

        mock_flavors.assert_called_once_with(app.compute_client)
        expected_flavors = [('id', 'name', 1, 2, 3)]
        self.assertEqual(expected_flavors, result)

    @mock.patch.object(resource_provider, 'get_allocations')
    @mock.patch.object(resource_provider, 'get_inventories')
    @mock.patch.object(resource_provider, 'get_all')
    def test_get_all_inventories_and_usage(self, mock_grp, mock_gi, mock_ga):
        mock_grp.return_value = [
            resource_provider.ResourceProvider('uuid1', 'name1'),
            resource_provider.ResourceProvider('uuid2', 'name2'),
            resource_provider.ResourceProvider('uuid3', 'name3')]
        fake_r = [
            resource_provider.ResourceClassAmount("CUSTOM_FOO", 3),
            resource_provider.ResourceClassAmount("CUSTOM_BAR", 2),
        ]
        mock_ga.side_effect = [
            [resource_provider.Allocation("uuid1", "consumer_uuid1", fake_r)],
            [],
            [resource_provider.Allocation("uuid1", "consumer_uuid2", fake_r)],
        ]
        mock_gi.side_effect = [
            [resource_provider.Inventory("uuid1", "VCPU", 10),
             resource_provider.Inventory("uuid1", "DISK_GB", 5)],
            [],
            [resource_provider.Inventory("uuid1", "VCPU", 10),
             resource_provider.Inventory("uuid1", "DISK_GB", 6)],
        ]
        app = mock.Mock()

        result = list(utils.get_all_inventories_and_usage(app))

        mock_grp.assert_called_once_with(app.placement_client)
        self.assertEqual(3, mock_gi.call_count)
        self.assertEqual(3, mock_ga.call_count)

        self.assertEqual([
            ('name1', 'DISK_GB:5, VCPU:10', 'consumer_uuid1'),
            ('name2', '', ''),
            ('name3', 'DISK_GB:6, VCPU:10', 'consumer_uuid2'),
        ], result)

    @mock.patch.object(resource_provider, 'get_allocations')
    @mock.patch.object(resource_provider, 'get_inventories')
    @mock.patch.object(resource_provider, 'get_all')
    @mock.patch.object(flavors, 'get_all')
    def test_group_inventories(self, mock_flav, mock_grp, mock_gi, mock_ga):
        mock_flav.return_value = [
            flavors.Flavor(id="id1", name="flavor1",
                           vcpus=1, ram_mb=2, disk_gb=3),
            flavors.Flavor(id="id2", name="flavor2",
                           vcpus=1, ram_mb=2, disk_gb=30),
            flavors.Flavor(id="id3", name="flavor3",
                           vcpus=1, ram_mb=2, disk_gb=3),
        ]
        mock_grp.return_value = [
            resource_provider.ResourceProvider('uuid1', 'name1'),
            resource_provider.ResourceProvider('uuid2', 'name2'),
            resource_provider.ResourceProvider('uuid3', 'name3')]
        fake_r = [
            resource_provider.ResourceClassAmount("VCPU", 1),
            resource_provider.ResourceClassAmount("MEMORY_MB", 2),
            resource_provider.ResourceClassAmount("DISK_GB", 3),
        ]
        mock_ga.side_effect = [
            [resource_provider.Allocation("uuid1", "consumer_uuid1", fake_r)],
            [],
            [resource_provider.Allocation("uuid3", "consumer_uuid2", fake_r)],
        ]
        mock_gi.side_effect = [
            [resource_provider.Inventory("uuid1", "VCPU", 1),
             resource_provider.Inventory("uuid1", "MEMORY_MB", 2),
             resource_provider.Inventory("uuid1", "DISK_GB", 3)],
            [resource_provider.Inventory("uuid1", "VCPU", 1),
             resource_provider.Inventory("uuid1", "MEMORY_MB", 2),
             resource_provider.Inventory("uuid1", "DISK_GB", 30)],
            [resource_provider.Inventory("uuid1", "VCPU", 1),
             resource_provider.Inventory("uuid1", "MEMORY_MB", 2),
             resource_provider.Inventory("uuid1", "DISK_GB", 3)],
        ]
        app = mock.Mock()

        result = list(utils.group_all_inventories(app))

        self.assertEqual(2, len(result))
        expected = [
            ('VCPU:1,MEMORY_MB:2,DISK_GB:30', 1, 0, 1, 'flavor2'),
            ('VCPU:1,MEMORY_MB:2,DISK_GB:3', 2, 2, 0, 'flavor1, flavor3')
        ]
        self.assertEqual(expected, result)

    @mock.patch.object(server, 'get')
    @mock.patch.object(resource_provider, 'get_all_allocations')
    @mock.patch.object(resource_provider, 'get_all')
    @mock.patch.object(utils, '_get_now')
    def test_get_allocation_list(self, mock_now, mock_rps, mock_allocations,
                                 mock_server):
        mock_now.return_value = datetime.datetime(2017, 3, 2)

        mock_rps.return_value = [
            resource_provider.ResourceProvider("uuid1", "name1"),
            resource_provider.ResourceProvider("uuid2", "name2")
        ]
        mock_allocations.return_value = [
            resource_provider.Allocation(
                "uuid1", "consumer_uuid2", [
                    resource_provider.ResourceClassAmount("DISK_GB", 10),
                    resource_provider.ResourceClassAmount("MEMORY_MB", 20),
                    resource_provider.ResourceClassAmount("VCPU", 30)]),
            resource_provider.Allocation(
                "uuid2", "consumer_uuid1", [
                    resource_provider.ResourceClassAmount("DISK_GB", 10),
                    resource_provider.ResourceClassAmount("MEMORY_MB", 20),
                    resource_provider.ResourceClassAmount("VCPU", 30)]),
        ]
        mock_server.side_effect = [
            server.Server("consumer_uuid2", "name",
                          datetime.datetime(2017, 3, 1),
                          "user_id", "project_id", "flavor"),
            server.Server("consumer_uuid2", "name",
                          datetime.datetime(2017, 3, 1),
                          "user_id", "project_id", "flavor"),
        ]
        app = mock.Mock()

        result = utils.get_allocation_list(app)

        mock_rps.assert_called_once_with(app.placement_client)
        self.assertEqual(2, len(result))
        expected1 = utils.AllocationList(
            'name1', 'consumer_uuid2',
            'DISK_GB:10, MEMORY_MB:20, VCPU:30',
            'flavor', 1, 'project_id', 'user_id')
        self.assertEqual(expected1, result[0])
        expected2 = utils.AllocationList(
            'name2', 'consumer_uuid1',
            'DISK_GB:10, MEMORY_MB:20, VCPU:30',
            'flavor', 1, 'project_id', 'user_id')
        self.assertEqual(expected2, result[1])
