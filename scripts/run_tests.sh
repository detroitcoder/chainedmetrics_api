

tag=$RANDOM
echo $tag
docker build -t test:$tag .

docker run \
-a stdout -a stderr -p 5050:5050 -it \
-e DB_PASS=$DEV_DB_PASS -e JWT_SECRET_KEY=stay_safe_out_there -e MAILCHIMP_API_KEY=$MAILCHIMP_API_KEY\
 -e GMAIL_PASS=$MAILCHIMP_API_KEY -v ~/chained_metrics_api:/src/chainedmetrics_api \
 -w /src/chainedmetrics_api/src \
 --entrypoint /opt/conda/bin/conda \
 test:$tag \
 run --no-capture-output -n app pytest