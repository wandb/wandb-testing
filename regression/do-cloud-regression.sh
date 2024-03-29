#!/bin/bash

# Find testing AWS creds in 1password Eng Vault: "wandb-testing: aws-creds.sh"
#AWS_CREDENTIALS=~/.config/wandb-testing/aws-creds.sh
#source $AWS_CREDENTIALS
echo $GCP_SERVICE_ACCOUNT_JSON_DECODED > /tmp/gcp-service-account.json
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-service-account.json
export GCLOUD_PROJECT=wandb-client-cicd

EXTRA=${*:-"tests/main/"}
parent_dir=$(dirname "$0")
pushd "$parent_dir"
./do-main-regression.sh $EXTRA
# capture exit code
exit_code=$?
popd
exit $exit_code
