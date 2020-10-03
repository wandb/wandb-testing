#!/usr/bin/env python

# Common code (refactor into regression framework at some point)
import os
import wandb
run_id = os.environ.get("WANDB_RUN_ID")
project = os.environ.get("WANDB_PROJECT") or "regression"
api = wandb.Api()
#last_run = api.run("%s/%s" % (project, run_id))

#
# Test Checks
#
run_group = os.environ.get("WANDB_RUN_GROUP")
run_name = os.environ.get("WANDB_NAME")
project = "{}-raytune-{}-{}".format(project, run_group, run_name)
runs = list(api.runs(project))
assert len(runs) == 6
uniq = {(r.config["lr"], r.config["momentum"]) for r in runs}
assert len(uniq) == 6
for r in runs:
    assert(r.summary_metrics["mean_accuracy"] > 0)
