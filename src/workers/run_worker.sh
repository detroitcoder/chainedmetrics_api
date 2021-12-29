docker run \
 -i --log-driver=none -a stdin -a stdout -a stderr \
 -e CHAINEDMETRICS_ENV=$CHAINEDMETRICS_ENV \
 -e PRIVATE_KEY=$PRIVATE_KEY \
 -e WEB3_INFURA_PROJECT_ID=$WEB3_INFURA_PROJECT_ID \
 -e DB_PASS=$DEV_DB_PASS \
 faucet_worker:1