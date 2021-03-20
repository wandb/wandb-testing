#!/usr/bin/env python

import sys
import os

download_dir = None
args = sys.argv[1:]
if len(args) >= 1:
    download_dir = args[0]

if download_dir:
    try:
        os.makedirs(download_dir)
    except FileExistsError:
        pass
    os.chdir(download_dir)

wandb_git = os.environ.get("WANDB_REGRESSION_CLIENT_GIT")
wandb_hash = os.environ.get("WANDB_REGRESSION_CLIENT_GITHASH")
if wandb_git:
    print("git:", wandb_git, file=sys.stderr)
    os.system("git clone {}".format(wandb_git))
    if wandb_hash:
        print("hash:", wandb_hash, file=sys.stderr)
        # TODO: dont hardcode this
        os.chdir("client")
        os.system("git checkout {}".format(wandb_hash))
