docker run \
-a stdout -a stderr -p 5050:5050 -it \
-e DB_PASS=$DEV_DB_PASS \
 -v ~/chained_metrics_api:/src/chainedmetrics_api \
 -w /src/chainedmetrics_api/src \
 --entrypoint /opt/conda/bin/conda \
 registry.digitalocean.com/chainedmetrics/chainedmetrics_api:$1 \
 run --no-capture-output -n app flask run -p 5050 -h 0.0.0.0