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
assert last_run.summary_metrics["this"] == "that"
assert last_run.summary_metrics["yes"] == 2
assert last_run.config["extra3"] == 33
assert last_run.config["init1"] == 11
assert last_run.config["init2"] == 22
