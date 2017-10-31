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
import os
import time

Metric = collections.namedtuple(
    "Metric", ("name", "value", "value_meta", "dimensions"))

SEND_METRICS = 'OS_CAPACITY_SEND_METRICS' in os.environ


def send_metrics(monitoring_client, metrics):
    if not SEND_METRICS:
        return

    timestamp = time.time() * 1000
    formatted_metrics = []
    for metric in metrics:
        formatted_metrics.append({
            "name": "os_capacity.%s" % metric.name,
            "value": float(metric.value),
            "timestamp": timestamp,
            "value_meta": metric.value_meta,
            "dimensions": metric.dimensions,
        })
    response = monitoring_client.post("/metrics", json=formatted_metrics)
    if not response:
        raise Exception("Had trouble talking to monasca %s" % response)
