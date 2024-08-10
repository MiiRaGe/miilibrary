#! /bin/sh

docker buildx build -f Dockerfile --platform linux/arm64 -t miirage/rpi-cluster:miilibrary-$1 -t miirage/rpi-cluster:miilibrary-latest --push .
