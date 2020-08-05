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
assert last_run.summary_metrics["global_step"] == 4
assert last_run.summary_metrics["train/global_step"] == 4
assert last_run.summary_metrics["validation/global_step"] == 4
assert last_run.summary_metrics["validation/epoch_loss"] > 0
assert last_run.summary_metrics["validation/epoch_accuracy"] > 0
