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
assert last_run, "can not find run"
assert last_run.state == "finished"
assert last_run.project == project

#
# Test Checks
#
video = last_run.summary_metrics["videos"]
assert video.get("_type") == "video-file"
assert video.get("size") > 0

# files are not stable in gorilla for some time
# so lets poll files for a minute
# file_names = set([f.name for f in last_run.files()])
# assert video.get("path") in file_names

import time
found = False
start_time = time.time()
while time.time() < start_time + 60 * 5:
    video = last_run.summary_metrics["videos"]
    assert video.get("_type") == "video-file"
    assert video.get("size") > 0
    video_file = video.get("path")

    file_names = set([f.name for f in last_run.files()])
    print("Looking for:", video_file, time.time() - start_time, file_names)
    if video_file in file_names:
        found = True
        break
    time.sleep(5)
assert found
