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
assert last_run.config.get("dropout") == 0.2, "we have config"
assert last_run.summary_metrics["accuracy"] > 0, "we have accuracy"
assert last_run.summary_metrics["loss"] > 0
assert last_run.summary_metrics["epoch"] == 9
files = set([f.name for f in last_run.files()])
assert 'code/examples/wandb-resume/train-auto-resume.py' in files, "codesaving worked"
