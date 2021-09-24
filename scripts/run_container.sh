docker run \
-a stdout -a stderr -p 5050:5050 -it \
-e DB_PASS=$DEV_DB_PASS -e JWT_SECRET_KEY=stay_safe_out_there -e MAILCHIMP_API_KEY=$MAILCHIMP_API_KEY\
 -e GMAIL_PASS=$MAILCHIMP_API_KEY \
 registry.digitalocean.com/chainedmetrics/chainedmetrics_api:$1 
