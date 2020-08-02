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
assert last_run.summary_metrics["global_step"] == 14999
assert last_run.summary_metrics["training loss"] > 0
image1 = last_run.summary_metrics["four_fashion_mnist_images"]
assert image1.get("_type") == "images"
assert image1.get("count") == 1
image2 = last_run.summary_metrics["predictions vs. actuals"]
assert image2.get("_type") == "images"
assert image2.get("count") == 1
