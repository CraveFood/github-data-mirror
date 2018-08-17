#!/bin/bash

docker exec -ti github-data-mirror_webhook_1 /bin/bash -c "python3 src/manage.py $*"
