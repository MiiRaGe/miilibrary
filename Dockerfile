FROM python:3.12.3-bookworm

# unrar (non-free) is needed by the filesystem worker, archives are extracted locally on the NAS
RUN sed -i 's/^Components: main$/Components: main non-free/' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends unrar \
    && rm -rf /var/lib/apt/lists/*

ADD requirements.txt /

RUN pip install --upgrade pip && pip install --no-input --upgrade --force-reinstall -r requirements.txt

ENV TZ=Europe/Stockholm

COPY . /app

WORKDIR /app

EXPOSE 5555
EXPOSE 8000
