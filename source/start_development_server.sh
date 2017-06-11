#!/usr/bin/env bash
set -e


docker build -t test/nc_assessment_executor .
docker run \
    --env NC_CONFIGURATION=development \
    -p5000:5000 \
    -v$(pwd)/nc_assessment_executor:/nc_assessment_executor \
    test/nc_assessment_executor
