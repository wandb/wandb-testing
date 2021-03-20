#!/bin/bash
export SAGEMAKER_ROLE="arn:aws:iam::618469898284:role/jeff-sagemaker"
time ./do-cloud-regression.sh $*
