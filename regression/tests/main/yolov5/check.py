import os
import wandb
run_id = os.environ.get("WANDB_RUN_ID")
project = os.environ.get("WANDB_PROJECT") or "regression"
api = wandb.Api()
last_run = api.run("%s/%s" % (project, run_id))

#
# Test Checks
#
assert last_run.summary_metrics["metrics/precision"] > 0
assert last_run.summary_metrics["metrics/recall"] > 0
assert last_run.summary_metrics["train/box_loss"] > 0
