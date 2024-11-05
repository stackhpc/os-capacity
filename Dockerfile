FROM ubuntu:24.04

RUN apt-get update && apt-get upgrade -y && apt-get install python3-pip tini -y && apt-get clean

COPY ./requirements.txt /opt/os-capacity/requirements.txt
RUN pip install -U -r /opt/os-capacity/requirements.txt

COPY ./os_capacity/prometheus.py /opt/os-capacity/prometheus.py
ENTRYPOINT ["tini", "--"]
CMD ["python3", "-u", "/opt/os-capacity/prometheus.py"]
