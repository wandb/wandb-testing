#!/usr/bin/env python

# Common code (refactor into regression framework at some point)
import os
import wandb
project = os.environ.get("WANDB_PROJECT") or "regression"
#run_group = os.environ.get("WANDB_RUN_GROUP")
#job_type = os.environ.get("WANDB_JOB_TYPE")
name = os.environ.get("WANDB_NAME")
notes = os.environ.get("WANDB_NOTES")
api = wandb.Api()
runs = api.runs(project)
last_run = next(runs, None)
assert last_run, "can not find run"
assert last_run.state == "finished"
assert last_run.project == project
#assert last_run.group == run_group
#assert last_run.job_type == job_type
assert last_run.name == name, "Mismatch {} != {}".format(last_run.name, name)
assert last_run.notes == notes, "Mismatch {} != {}".format(last_run.notes, notes)

#
# Test Checks
#
video = last_run.summary_metrics["videos"]
assert video.get("_type") == "video-file"
assert video.get("size") > 0
file_names = set([f.name for f in last_run.files()])
assert video.get("path") in file_names
