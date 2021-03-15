#!/usr/bin/env python

import os
import sys

# https://github.com/pytorch/vision/issues/1938#issuecomment-797711160

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

os.system("wget -O MNIST.tar.gz https://activeeon-public.s3.eu-west-2.amazonaws.com/datasets/MNIST.new.tar.gz")
# os.system("wget -O MNIST.tar.gz https://activeeon-public.s3.eu-west-2.amazonaws.com/datasets/MNIST.old.tar.gz")

os.system("tar -zxvf MNIST.tar.gz")
print("Files downloaded to:", os.path.abspath(os.getcwd()), file=sys.stderr)
