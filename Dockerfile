FROM ubuntu:24.04 AS build-image

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install python3-venv python3-dev gcc git -y && \
    rm -rf /var/lib/apt/lists/*

# build into a venv we can copy across
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt /os-capacity/requirements.txt
RUN pip install -U pip setuptools
RUN pip install --requirement /os-capacity/requirements.txt

COPY . /os-capacity
RUN pip install -U /os-capacity

#
# Now the image we run with
#
FROM ubuntu:24.04 AS run-image

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends python3 tini ca-certificates -y && \
    rm -rf /var/lib/apt/lists/*

# Copy accross the venv
COPY --from=build-image /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create the user that will be used to run the app
ENV APP_UID=1001
ENV APP_GID=1001
ENV APP_USER=app
ENV APP_GROUP=app
RUN groupadd --gid $APP_GID $APP_GROUP && \
    useradd \
      --no-create-home \
      --no-user-group \
      --gid $APP_GID \
      --shell /sbin/nologin \
      --uid $APP_UID \
      $APP_USER

USER $APP_UID
ENTRYPOINT ["tini", "--"]
CMD ["os_capacity"]
