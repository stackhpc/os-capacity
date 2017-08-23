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
from os_capacity.tests.unit import fakes
from os_capacity import utils


FAKE_ALLOCATIONS = {
    'c1d70ef7-f26b-4147-bcf9-0fd91ddaf8f6': {
        'resources': {
            'DISK_GB': 371, 'MEMORY_MB': 131072, 'VCPU': 64}
    }
}
FAKE_ALLOCATIONS_RESPONSE = {
    'allocations': FAKE_ALLOCATIONS,
    'resource_provider_generation': 43,
}


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

    def test_get_resource_providers(self):
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fakes.RESOURCE_PROVIDER_RESPONSE
        app = mock.MagicMock()
        app.placement_client.get.return_value = fake_response

        result = utils._get_resource_providers(app)

        app.placement_client.get.assert_called_once_with("/resource_providers")
        self.assertEqual([(fakes.RESOURCE_PROVIDER['uuid'], 'name1')], result)

    def test_get_inventories(self):
        fake_rps = [('uuid1', 'name1'), ('uuid2', 'name2')]
        fake_ironic_inventories = {'inventories': {
            'DISK_GB': {
                'allocation_ratio': 1.0,
                'max_unit': 10,
                'min_unit': 1,
                'reserved': 0,
                'step_size': 1,
                'total': 10},
            'MEMORY_MB': {'max_unit': 20},
            'VCPU': {'max_unit': 30},
        }}
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fake_ironic_inventories
        app = mock.MagicMock()
        app.placement_client.get.return_value = fake_response

        result = utils._get_inventories(app, fake_rps)

        app.placement_client.get.assert_called_with(
            "/resource_providers/uuid2/inventories")
        self.assertEqual({
            'uuid1': {'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 30},
            'uuid2': {'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 30},
        }, result)

    @mock.patch.object(utils, '_get_allocations')
    @mock.patch.object(utils, '_get_inventories')
    @mock.patch.object(utils, '_get_resource_providers')
    def test_get_all_inventories_and_usage(self, mock_grp, mock_gi, mock_a):
        fake_rps = [('uuid1', 'name1'), ('uuid2', 'name2'),
                    ('uuid3', 'name3')]
        mock_grp.return_value = fake_rps
        fake_inventories = {
            'uuid1': {'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 30},
            'uuid2': {},
            'uuid3': {'DISK_GB': 10, 'MEMORY_MB': 20, 'VCPU': 30},
        }
        mock_gi.return_value = fake_inventories
        fake_allocations = {
            'uuid1': {"server-uuid1": {
                'DISK_GB': 371, 'MEMORY_MB': 131072, 'VCPU': 64}},
            'uuid3': {},
        }
        mock_a.return_value = fake_allocations

        result = list(utils.get_all_inventories_and_usage(mock.Mock()))

        self.assertEqual([
            ('uuid1', 'name1', 30, 20, 10, True),
            ('uuid2', 'name2', None, None, None, False),
            ('uuid3', 'name3', 30, 20, 10, False),
        ], result)

    def test_group_inventories(self):
        fake_all_inventories = [
            ('uuid1', 'name1', 30, 20, 10, True),
            ('uuid2', 'name2', 0, 0, 0, False),
            ('uuid3', 'name3', 30, 20, 10, False),
        ]
        fake_flavors = [
            ('uuid1', 'test1', 30, 20, 10),
            ('uuid2', 'test2', 30, 20, 10),
            ('uuid3', 'test3', 8, 2048, 30),
        ]

        result = list(utils.group_all_inventories(
            fake_all_inventories, fake_flavors))

        self.assertEqual(2, len(result))
        self.assertEqual([
            ('VCPU:30,MEMORY_MB:20,DISK_GB:10', 2, 1, 1, "test1, test2"),
            ('VCPU:0,MEMORY_MB:0,DISK_GB:0', 1, 0, 1, '')], result)

    def test_get_allocations(self):
        fake_rps = [('uuid1', 'name1')]
        fake_response = mock.MagicMock()
        fake_response.json.return_value = FAKE_ALLOCATIONS_RESPONSE
        app = mock.MagicMock()
        app.placement_client.get.return_value = fake_response

        result = utils._get_allocations(app, fake_rps)

        app.placement_client.get.assert_called_once_with(
            "/resource_providers/uuid1/allocations")
        self.assertEqual({'uuid1': FAKE_ALLOCATIONS}, result)

    @mock.patch.object(utils, '_get_now')
    def test_get_allocation_list(self, mock_now):
        fake_response = mock.MagicMock()
        fake_response.json.side_effect = [
            fakes.RESOURCE_PROVIDER_RESPONSE, FAKE_ALLOCATIONS_RESPONSE]
        app = mock.MagicMock()
        app.placement_client.get.return_value = fake_response

        fake_compute_response = mock.MagicMock()
        fake_compute_response.json.return_value = fakes.SERVER_RESPONSE
        app.compute_client.get.return_value = fake_compute_response

        mock_now.return_value = datetime.datetime(2017, 3, 1)

        result = utils.get_allocation_list(app)

        rp_uuid = fakes.RESOURCE_PROVIDER['uuid']
        app.placement_client.get.assert_called_with(
            "/resource_providers/%s/allocations" % rp_uuid)
        self.assertEqual(1, len(result))
        expected = (
            fakes.RESOURCE_PROVIDER['name'], FAKE_ALLOCATIONS.keys()[0],
            'DISK_GB:371, MEMORY_MB:131072, VCPU:64',
            fakes.SERVER['flavor']['id'], 14,
            fakes.SERVER['tenant_id'], fakes.SERVER['user_id'])
        self.assertEqual(expected, result[0])
