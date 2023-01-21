#!/bin/bash
export SAGEMAKER_ROLE="arn:aws:iam::618469898284:role/jeff-sagemaker"

EXTRA=${*:-"tests/sagemaker-beta/"}
parent_dir=$(dirname "$0")
pushd "$parent_dir"
do-cloud-regression.sh $EXTRA
popd
