#!/bin/bash
set -e
WORKDIR=$HOME/work
LOCAL=$PWD
NAME=`basename $PWD`

PROJ=maskrcnn-benchmark
GITPROJ=https://github.com/facebookresearch/$PROJ
GITHASH=05feadff540c0d43e6752db0513d21e41038dbdb

# install
mkdir -p $WORKDIR/$NAME
cd $WORKDIR/$NAME
if [ ! -x $WORKDIR/$NAME/maskrcnn-benchmark ]; then
  git clone $GITPROJ
  cd $WORKDIR/$NAME/$PROJ
fi
# backup to last tested version
cd $WORKDIR/$NAME/$PROJ
git checkout $GITHASH

# unwind patches
cd $WORKDIR/$NAME/$PROJ
set +e
PATCHES=$(ls .patch-*.diff)
set -e
for x in $PATCHES; do
	patch -p1 -R <$x
	rm $x
done

# apply patches
PATCH="wandb-1.diff"
#PATCH="wandb-watch-param.diff"
#PATCH="wandb-watch-grad.diff"
#PATCH="wandb-watch-disabled.diff"
#PATCH="wandb-watch-none.diff"
#PATCH="wandb-disabled.diff"
#if [ ! -f $WORKDIR/$NAME/$PROJ/.patch-$PATCH ]; then
#	patch -p1 <$LOCAL/$PATCH
#	cp $LOCAL/$PATCH $WORKDIR/$NAME/$PROJ/.patch-$PATCH
#fi


# add files?
echo "Adding files..."
mkdir -p $WORKDIR/$NAME/$PROJ/wandb
cp $LOCAL/run.sh $WORKDIR/$NAME/$PROJ/wandb/
cp $LOCAL/wandb-1.diff $WORKDIR/$NAME/$PROJ/wandb/

# build
nvidia-docker build -t maskrcnn-benchmark docker/
TAG=`docker images --digests | grep ^maskrcnn-benc | awk '{print $4}'`
docker tag $TAG jeffwandb/maskrcnn-benchmark2
docker push jeffwandb/maskrcnn-benchmark2

# run
cd $WORKDIR/$NAME/$PROJ
./launch.sh


echo "Done."
