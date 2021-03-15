#!/usr/bin/env bash

# https://github.com/pytorch/vision/issues/1938#issuecomment-797711160
DIR=$1

if [ "x$DIR" != "x" ]; then
    cd $DIR
fi
wget -O MNIST.tar.gz https://activeeon-public.s3.eu-west-2.amazonaws.com/datasets/MNIST.new.tar.gz
tar -zxvf MNIST.tar.gz
