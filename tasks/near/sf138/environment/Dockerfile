FROM python:3.12.12-slim-bookworm AS python_3_12_12
FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates curl ripgrep less patch diffutils build-essential binutils pkg-config python3 libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev tzdata libbz2-1.0 libreadline8 libsqlite3-0 liblzma5 libgdbm6 libncursesw6 ncurses-term netbase gcc-11 g++-11 && rm -rf /var/lib/apt/lists/*
COPY --from=python_3_12_12 /usr/local/ /opt/python/3.12.12/
COPY . /opt/ssb/
WORKDIR /work
RUN /usr/bin/python3 /opt/ssb/install.py
RUN /usr/bin/python3 /opt/ssb/checkout.py
RUN mkdir -p /opt/ssb/bin && chmod +x /opt/ssb/dispatch.py && ln -s /opt/ssb/dispatch.py /opt/ssb/bin/python && ln -s /opt/ssb/dispatch.py /opt/ssb/bin/python3 && ln -s /opt/ssb/dispatch.py /opt/ssb/bin/pytest
ENV PATH="/opt/ssb/bin:/usr/local/bin:/usr/bin:/bin"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
RUN mkdir -p /opt/runtime/case-python/python/bin && ln -s /opt/ssb/dispatch.py /opt/runtime/case-python/python/bin/python && ln -s /opt/ssb/dispatch.py /opt/runtime/case-python/python/bin/python3 && ln -s /opt/ssb/dispatch.py /opt/runtime/case-python/python/bin/python3.12
RUN chmod +x /opt/ssb/rebuild-native.py
RUN /opt/ssb/rebuild-native.py /work/w00
RUN /opt/ssb/rebuild-native.py /work/w01
RUN /opt/ssb/rebuild-native.py /work/w02
RUN /opt/ssb/rebuild-native.py /work/w03
RUN /opt/ssb/rebuild-native.py /work/w04
RUN cd /work/w00 && python -c 'import pandas'
RUN cd /work/w01 && python -c 'import pandas'
RUN cd /work/w02 && python -c 'import pandas'
RUN cd /work/w03 && python -c 'import pandas'
RUN cd /work/w04 && python -c 'import pandas'
RUN useradd -m -s /bin/bash agent && chown -R agent:agent /work && chmod 700 /opt/focus-base
RUN /usr/bin/python3 -c 'import json,pathlib; p=pathlib.Path('"'"'/opt/ssb/environment.json'"'"'); c=json.loads(p.read_text()); c.pop('"'"'focus_workspace'"'"',None); c.pop('"'"'case_id'"'"',None); p.write_text(json.dumps(c))' && rm -rf /opt/ssb/checkout.py /opt/ssb/overlay-blobs
WORKDIR /work
