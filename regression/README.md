
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
```