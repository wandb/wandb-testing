#!/bin/bash
set -e
WORKDIR=$HOME/work
LOCAL=$PWD
NAME=`basename $PWD`

# env
#pip install --upgrade torch==1.0.0
#pip install --upgrade torch==1.0.1.post2
#pip install --upgrade torchvision==0.2.2.post3

pip install --upgrade  torch_nightly -f https://download.pytorch.org/whl/nightly/cu100/torch_nightly.html
pip install --upgrade  torchvision_nightly

# install
mkdir -p $WORKDIR/NVIDIA
cd $WORKDIR/NVIDIA
if [ ! -x $WORKDIR/NVIDIA/apex ]; then
  #git clone https://github.com/NVIDIA/apex.git
  cd $WORKDIR/NVIDIA/apex
  pip install -v --no-cache-dir --global-option="--cpp_ext" --global-option="--cuda_ext" .
fi
# git clone --recursive https://github.com/pytorch/pytorch

# env
#pip install --upgrade wandb==0.7.1

# patch
cd $WORKDIR/NVIDIA/apex/
set +e
PATCHES=$(ls .patch-*.diff)
set -e
for x in $PATCHES; do
	patch -p1 -R <$x
	rm $x
done
PATCH="wandb-watch-all.diff"
#PATCH="wandb-watch-param.diff"
#PATCH="wandb-watch-grad.diff"
#PATCH="wandb-watch-disabled.diff"
#PATCH="wandb-watch-none.diff"
#PATCH="wandb-disabled.diff"
if [ ! -f $WORKDIR/NVIDIA/apex/.patch-$PATCH ]; then
	patch -p1 <$LOCAL/$PATCH
	cp $LOCAL/$PATCH $WORKDIR/NVIDIA/apex/.patch-$PATCH
fi

# run
QUICK=""
#QUICK="--prof"
MODE="run"
#MODE="dryrun"
DESC=$(echo $PATCH | sed 's/[.]diff$//' | sed 's/^wandb-//')
cd $WORKDIR/NVIDIA/apex/examples/imagenet
#WANDB_MODE=$MODE WANDB_PROJECT=regression WANDB_RUN_GROUP="$NAME" WANDB_DESCRIPTION="$DESC" CUDA_VISIBLE_DEVICES=1 \
WANDB_MODE=$MODE WANDB_PROJECT=regression WANDB_RUN_GROUP="$NAME" WANDB_DESCRIPTION="$DESC" \
python main_amp.py $QUICK --epochs 3 -a resnet50 --b 296 --workers 4 --opt-level O3 /home/datasets/ImageNet/
#python main_amp.py $QUICK --epochs 2 -a resnet50 --b 112 --workers 4 --opt-level O3 /home/datasets/ImageNet/

#python -m torch.utils.bottleneck main_amp.py --prof -a resnet50 --b 112 --workers 0 --opt-level O3 /home/datasets/ImageNet/
#/usr/local/cuda-10.0/bin/nvprof python main_amp.py --prof -a resnet50 --b 112 --workers 0 --opt-level O3 /home/datasets/ImageNet/
