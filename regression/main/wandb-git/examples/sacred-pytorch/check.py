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
assert last_run.summary_metrics["accuracy"] > 90
assert last_run.summary_metrics["Batch_loss"] < 1
image1 = last_run.summary_metrics["Images"]
image1_type = image1.get("_type")
assert image1_type == "image-file"
# TODO: add artifact check
