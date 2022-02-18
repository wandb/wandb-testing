#!/usr/bin/env python

# Common code (refactor into regression framework at some point)
import os
import wandb
run_id = os.environ.get("WANDB_RUN_ID")
project = os.environ.get("WANDB_PROJECT") or "regression"
# hardcoded by test
project = "fastai-tabular"
api = wandb.Api()
last_run = api.run("%s/%s" % (project, run_id))

#
# Test Checks
#
assert last_run.summary_metrics["epoch"] == 2
assert last_run.summary_metrics["train_loss"] > 0
assert last_run.summary_metrics["valid_loss"] > 0
image1 = last_run.summary_metrics["Prediction Samples"]
assert image1.get("_type") == "table-file"
