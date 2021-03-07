#!/bin/bash
export AWS_ACCESS_KEY_ID=AKIAY775NXAWJSAQYUVQ
export AWS_SECRET_ACCESS_KEY=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
export AWS_DEFAULT_REGION=us-west-2
export GOOGLE_APPLICATION_CREDENTIALS=~/gcp-storage-creds-qa.json
export GCLOUD_PROJECT=jungle
time ./do-main-regression.sh $*
