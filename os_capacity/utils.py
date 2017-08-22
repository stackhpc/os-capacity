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


def get_capacity():
    return [{"flavor": "foo", "count": 1}]


def get_flavors(app):
    client = app.compute_client
    response = client.get("/flavors/detail").json()
    raw_flavors = response['flavors']
    return [(f['id'], f['name'], f['vcpus'], f['ram'], f['disk'])
            for f in raw_flavors]
