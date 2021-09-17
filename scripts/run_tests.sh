docker build -t test:$1 .

docker run \
-a stdout -a stderr -p 5050:5050 -it \
-e DB_PASS=invalid_pass -e JWT_SECRET_KEY=stay_safe_out_there\
 -v ~/chained_metrics_api:/src/chainedmetrics_api \
 -w /src/chainedmetrics_api/src \
 --entrypoint /opt/conda/bin/conda \
 test:$1 \
 run --no-capture-output -n app python -m unittest tests