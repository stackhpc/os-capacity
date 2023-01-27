FROM ubuntu:22.04

RUN apt-get update && apt-get upgrade -y && apt-get install python3-pip tini -y && apt-get clean

COPY . /opt/os-capacity
RUN pip install -U -e /opt/os-capacity

ENTRYPOINT ["tini", "-g", "--"]
CMD ["python3", "/opt/os-capacity/os_capacity/prometheus.py"]
