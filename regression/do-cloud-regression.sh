#!/bin/bash
AWS_CREDENTIALS=~/.config/wandb-testing/aws-creds.sh
source $AWS_CREDENTIALS
export GOOGLE_APPLICATION_CREDENTIALS=~/.config/wandb-testing/gcp-storage-creds-qa.json
export GCLOUD_PROJECT=jungle
time ./do-main-regression.sh $*
