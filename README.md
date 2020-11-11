# IRS lookup tool

Serverless implementation to check 990 status

### Deploy

To limit the 990 sync size, create a `.env` file with a list of EIN numbers:

    EIN_FILTER=812826681,<<EIN#>>,<<EIN#>>

If you don't do this, the app will try to download records for all non-profits!

To deploy, install justfile and run:

    just stage=dev deploy
     
Change stage to `production` for prod deploy 

#### Refresh 990s

990s will auto-refresh every 7 days. To manually refresh, run:

    sls invoke -f cron_refresh_990s --type Event --data '{"body": "{}", "headers": {"Content-Type": "application-json"}}'


To refresh a single year use:

    sls invoke -f cron_refresh_990s --type Event --data '{"body": "{}", "headers": {"Content-Type": "application-json"}}'


### Test

    npm install
    sls dynamodb install
    AWS_PROFILE=default SLS_DEBUG=* PYTHONPATH=./.serverless/requirements sls offline start

#### Fetch for EIN
`aws lambda invoke /dev/null \
   --cli-binary-format raw-in-base64-out \
   --payload '{"pathParameters": {"ein":"471417900"}}' \
   --endpoint-url http://localhost:3002 \
   --function-name irs-lookup-dev-http_fetch_990`
   
#### Reload 990s for Year
`aws lambda invoke /dev/null \
   --invocation-type Event \
   --cli-binary-format raw-in-base64-out \
   --payload '{"body": "{\"year\": \"2019\"}", "headers": {"Content-Type": "application-json"}}' \
   --endpoint-url http://localhost:3002 \
   --function-name irs-lookup-dev-cron_refresh_990s`