docker run \
-p 5050:5050 -it \
-e DB_PASS=$DEV_DB_PASS \
 -v ~/chained_metrics_api:/src/chainedmetrics_api \
 -w /src/chainedmetrics_api/src \
 registry.digitalocean.com/chainedmetrics/chainedmetrics_api:$1 \
 /bin/bash