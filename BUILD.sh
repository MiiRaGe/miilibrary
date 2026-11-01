#! /bin/sh

# arm64 for the raspberry pi cluster (web UI, beat, default worker), amd64 for the NAS (filesystem worker)
docker buildx build -f Dockerfile --platform linux/arm64,linux/amd64 -t miirage/rpi-cluster:miilibrary-$1 -t miirage/rpi-cluster:miilibrary-latest --push .
