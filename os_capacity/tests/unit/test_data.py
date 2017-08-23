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

import mock
import unittest

from os_capacity.data import flavors
from os_capacity.tests.unit import fakes


class TestFlavor(unittest.TestCase):

    def test_get_all(self):
        fake_response = mock.MagicMock()
        fake_response.json.return_value = fakes.FLAVOR_RESPONSE
        compute_client = mock.MagicMock()
        compute_client.get.return_value = fake_response

        result = flavors.get_all(compute_client)

        expected_flavors = [(fakes.FLAVOR['id'], 'compute-GPU', 8, 2048, 30)]
        self.assertEqual(expected_flavors, result)
