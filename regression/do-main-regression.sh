#!/bin/bash
ulimit -n 4096
# get WANDB API KEY for ray tests (for now)
if [ "$WANDB_API_KEY" == "" ]; then
   WANDB_API_KEY=`cat ~/.netrc  | grep "machine api.wandb.ai" -A 2 | grep password | awk '{print $2}'`
fi
if [ "$WANDB_API_KEY" == "" ]; then
   echo "Make sure api key is set"
   exit 1
fi
# clean up temporary dir
rm -rf tmp-cli/
export WANDB_API_KEY=$WANDB_API_KEY

EXTRA=${*:-"tests/main/"}
parent_dir=$(dirname "$0")
pushd "$parent_dir"
time ./regression.py --spec :~base:~broken $EXTRA
# capture exit code
exit_code=$?
popd
exit $exit_code
