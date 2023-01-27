os-capacity
===========

This is a prototype tool to extract capacity information.

Install
-------

First lets get the code downloaded:

.. code::

    git clone https://github.com/JohnGarbutt/os-capacity.git
    cd os-capacity

Now lets get that installed inside a virtual environment:

.. code::

    python3 -m virtualenv .venv
    source .venv/bin/activate
    pip install -U .

Prometheus Exporter
-------------------

Assuming you have clouds.yaml in the right place,
you can run the exporter doing something like this:

.. code::

   export OS_CLIENT_CONFIG_FILE=myappcred.yaml
   export OS_CLOUD=openstack

   ./os_capacity/prometheus.py &
   curl localhost:9000 > mytestrun
   cat mytestrun
