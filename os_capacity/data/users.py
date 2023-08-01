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


def get_all(identity_client):
    response = identity_client.get("/users").json()
    raw_users = response['users']
    return {u['id']: u['name'] for u in raw_users}


def get_all_projects(identity_client):
    response = identity_client.get("/projects").json()
    raw_projects = response['projects']
    return {u['id']: u['name'] for u in raw_projects}
