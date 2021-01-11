#!/usr/bin/env python

# Common code (refactor into regression framework at some point)
import os
import wandb
run_id = os.environ.get("WANDB_RUN_ID")
project = os.environ.get("WANDB_PROJECT") or "regression"
api = wandb.Api()
last_run = api.run("%s/%s" % (project, run_id))

#
# Test Checks
#
assert last_run.summary_metrics["sum2"] == 4
assert last_run.summary_metrics["sum3"] == 3
assert last_run.summary_metrics["this"] == 4
assert last_run.config["parm5"] == 55
assert last_run.config["parm6"] == 66
