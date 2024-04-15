#! /bin/sh

docker buildx build -f Dockerfile.celerybeat --platform linux/arm64 -t miirage/rpi-cluster:miilibrary-celery-beat-$1 -t miirage/rpi-cluster:miilibrary-celery-beat-latest --push .
docker buildx build -f Dockerfile.celeryworker --platform linux/arm64 -t miirage/rpi-cluster:miilibrary-celery-worker-$1 -t miirage/rpi-cluster:miilibrary-celery-worker-latest --push .
docker buildx build -f Dockerfile.webserver --platform linux/arm64 -t miirage/rpi-cluster:miilibrary-webserver-$1 -t miirage/rpi-cluster:miilibrary-webserver-latest --push .
docker buildx build -f Dockerfile.flower --platform linux/arm64 -t miirage/rpi-cluster:miilibrary-flower-$1 -t miirage/rpi-cluster:miilibrary-flower-latest --push .
