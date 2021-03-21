#!/bin/bash

# Find testing AWS creds in 1password Eng Vault: "wandb-testing: aws-creds.sh"
AWS_CREDENTIALS=~/.config/wandb-testing/aws-creds.sh
source $AWS_CREDENTIALS
export GOOGLE_APPLICATION_CREDENTIALS=~/.config/wandb-testing/gcp-storage-creds-qa.json
export GCLOUD_PROJECT=jungle

EXTRA=${*:-"tests/main/"}
./do-main-regression.sh $EXTRA
