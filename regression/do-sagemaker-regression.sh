#!/bin/bash
export SAGEMAKER_ROLE="arn:aws:iam::618469898284:role/jeff-sagemaker"

EXTRA=${*:-"tests/sagemaker-beta/"}
./do-cloud-regression.sh $EXTRA
