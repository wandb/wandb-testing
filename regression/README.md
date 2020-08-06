
## To run the regression:
```
    ./regression.py .
```

## To choose your branch:
```
    ./regression --cli_branch feature/this-is-my-branch
```

## Helper scripts:
```
    # Run main regression (Takes approximately 2 hours)
    # pass additional args to the script like "cli_branch"
    ./do_main_regression.sh
```

## Mac setup (not necessary for Linux)
```
brew install coreutils
```

## Requirements:

- python3
- pyenv
- everything in: requirements.txt
- ~/.netrc (logged in to wandb)

## Sample output:

```
Failed runs:
    0: k-examples-mnist-cnn:base_py27
    1: k-examples-mnist-cnn:init_py27
    2: k-examples-mnist-cnn:callback_py27
    3: wandb-standalone-simpsons_data_frames:init_py27
    4: wandb-standalone-simpsons_data_frames:init_py36
    5: wandb-standalone-mixed-keras:init_py27
```

## Review the results:

At the end of the regression it will spit out some info about failed runs,  then click through the UI for your regression group (stored under project "regression") to see if runs logged something that looks reasonable.  compare to previous releases.   I usually only spot check the stuff that i know had a risk of breaking.

## Other run commands:
```
   # Run a specific test
   ./regression.py main/ --spec wandb-examples-pt-cnn-mnist:full:py36
   # Not sure what will run, use dryrun
   ./regression.py --dryrun main/ --spec ::py27
   # Run a regression with cling
   ./regression.py --spec ::~broken --cli_base wandb-ng --cli_repo wandb/client-ng.git main/

```

## Create a new test:

1. Make a new directory in `main/` or `magic/` close to other similar tests

2. Create `regression.yaml` file in that directory

(Example from https://github.com/wandb/wandb-testing/blob/master/regression/main/wandb-git/examples/tensorboard-tf2-kerasfit/regression.yaml)

```
version: 0.0                                       # <- Version of this file format
name: wandb-examples-tensorboard-tf2-kerasfit      # <- What the test will be called
sources:
    - wandb-examples:                              # <- Identifier for the sourcetree to be checked out
        url: git@github.com:wandb/examples.git     # <- Git url to checkout
        base: examples                             # <- Base directory where git is checked out
        #hash: 
launch:
    path: examples/tensorboard-tf2-kerasfit        # <- Change directory before running command
    command:                                       # <- Command args specified as an array of arguments
        - python
        - train.py
components:
    tb:                                            # <- Identifier for a test requirement
        pip:
            - tensorboard                          # <- List of packages to install
variants:
    - init:                                        # <- Identifier of the test to run (appended to test name)
        - python3s                                 # <- Defined in regression-config.yaml, test multiple versions of python3
        - wandb-cli                                # <- Defined in regression-config.yaml, install wandb library
        - tf2                                      # <- Defined in regression-config.yaml, use tensorflow 2+ (multiple versions)
        - tb                                       # <- require "tb" component defined above (move to regression-config.yaml for reuse)
check:
    command:
        - python                                   # <- Run this command after the test is finished to validate the run
        - check.py
```

3. Add `check.py` script

```
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
```
