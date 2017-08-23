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
from os_capacity.tests.unit import fakes


class TestFlavor(unittest.TestCase):

    def test_get_all(self):
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fakes.FLAVOR_RESPONSE
        compute_client = mock.MagicMock()
        compute_client.get.return_value = fake_response

        result = flavors.get_all(compute_client)

        compute_client.get.assert_called_once_with("/flavors/detail")
        expected_flavors = [(fakes.FLAVOR['id'], 'compute-GPU', 8, 2048, 30)]
        self.assertEqual(expected_flavors, result)


class TestResourceProvider(unittest.TestCase):

    def test_get_all(self):
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fakes.RESOURCE_PROVIDER_RESPONSE
        placement_client = mock.MagicMock()
        placement_client.get.return_value = fake_response

        result = resource_provider.get_all(placement_client)

        placement_client.get.assert_called_once_with("/resource_providers")
        self.assertEqual([(fakes.RESOURCE_PROVIDER['uuid'], 'name1')], result)


class TestInventory(unittest.TestCase):

    def test_get_inventories(self):
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fakes.INVENTORIES_RESPONSE
        client = mock.MagicMock()
        client.get.return_value = fake_response

        rp = resource_provider.ResourceProvider("uuid", "name")

        result = resource_provider.get_inventories(client, rp)

        client.get.assert_called_once_with(
            "/resource_providers/uuid/inventories")
        self.assertEqual(3, len(result))
        disk = resource_provider.Inventory("uuid", "DISK_GB", 10)
        self.assertIn(disk, result)
        mem = resource_provider.Inventory("uuid", "MEMORY_MB", 20)
        self.assertIn(mem, result)
        vcpu = resource_provider.Inventory("uuid", "VCPU", 30)
        self.assertIn(vcpu, result)

    @mock.patch.object(resource_provider, 'get_all')
    def test_get_all_inventories(self, mock_get_all):
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fakes.INVENTORIES_RESPONSE
        client = mock.MagicMock()
        client.get.return_value = fake_response

        rp1 = resource_provider.ResourceProvider("uuid1", "name1")
        rp2 = resource_provider.ResourceProvider("uuid2", "name2")
        mock_get_all.return_value = [rp1, rp2]

        result = resource_provider.get_all_inventories(client)

        mock_get_all.assert_called_once_with(client)
        client.get.assert_called_with(
            "/resource_providers/uuid2/inventories")
        self.assertEqual(6, len(result))
        disk1 = resource_provider.Inventory("uuid1", "DISK_GB", 10)
        self.assertIn(disk1, result)
        disk2 = resource_provider.Inventory("uuid2", "DISK_GB", 10)
        self.assertIn(disk2, result)


class TestAllocations(unittest.TestCase):

    def test_get_allocations(self):
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fakes.ALLOCATIONS_RESPONSE
        client = mock.MagicMock()
        client.get.return_value = fake_response

        rp = resource_provider.ResourceProvider("uuid", "name")

        result = resource_provider.get_allocations(client, rp)

        self.assertEqual(1, len(result))
        expected = resource_provider.Allocation(
            "uuid", "consumer_uuid", [
                resource_provider.ResourceClassAmount("DISK_GB", 10),
                resource_provider.ResourceClassAmount("MEMORY_MB", 20),
                resource_provider.ResourceClassAmount("VCPU", 30)])
        self.assertEqual(expected, result[0])

    @mock.patch.object(resource_provider, 'get_all')
    def test_get_all_allocations(self, mock_get_all):
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fakes.ALLOCATIONS_RESPONSE
        client = mock.MagicMock()
        client.get.return_value = fake_response

        rp1 = resource_provider.ResourceProvider("uuid1", "name1")
        rp2 = resource_provider.ResourceProvider("uuid2", "name2")
        mock_get_all.return_value = [rp1, rp2]

        result = resource_provider.get_all_allocations(client)

        self.assertEqual(2, len(result))
        uuid1 = resource_provider.Allocation(
            "uuid1", "consumer_uuid", [
                resource_provider.ResourceClassAmount("DISK_GB", 10),
                resource_provider.ResourceClassAmount("MEMORY_MB", 20),
                resource_provider.ResourceClassAmount("VCPU", 30)])
        self.assertIn(uuid1, result)
        uuid2 = resource_provider.Allocation(
            "uuid1", "consumer_uuid", [
                resource_provider.ResourceClassAmount("DISK_GB", 10),
                resource_provider.ResourceClassAmount("MEMORY_MB", 20),
                resource_provider.ResourceClassAmount("VCPU", 30)])
        self.assertIn(uuid2, result)


class TestServer(unittest.TestCase):
    def test_parse_created(self):
        result = server._parse_created("2017-02-14T19:23:58Z")
        expected = datetime.datetime(2017, 2, 14, 19, 23, 58)
        self.assertEqual(expected, result)

    def test_get(self):
        mock_response = mock.Mock()
        mock_response.json.return_value = fakes.SERVER_RESPONSE
        compute_client = mock.Mock()
        compute_client.get.return_value = mock_response

        uuid = '9168b536-cd40-4630-b43f-b259807c6e87'
        result = server.get(compute_client, uuid)

        expected = server.Server(
            uuid=uuid,
            name='new-server-test',
            created=datetime.datetime(2017, 2, 14, 19, 23, 58),
            user_id='fake',
            project_id='6f70656e737461636b20342065766572',
            flavor_id='7b46326c-ce48-4e43-8aca-4f5ca00d5f37')
        self.assertEqual(expected, result)
