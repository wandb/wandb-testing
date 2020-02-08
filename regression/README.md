
To run the regression:
    regression.py .





----------------------------------
OLD:

https://github.com/pytorch/examples/tree/master/imagenet
    clone: git clone git@github.com:pytorch/examples.git pytorch-examples
    diff: pytorch-examples-imagenet.diff
    command: python main.py /home/datasets/ImageNet/
    dataset: ImageNet

https://github.com/ruotianluo/pytorch-faster-rcnn
    dataset: Coco


https://github.com/NVIDIA/apex
    clone: git clone git@github.com:NVIDIA/apex.git nvidia-apex
    dataset: ImageNet
    cd apex
    pip install -v --no-cache-dir --global-option="--cpp_ext" --global-option="--cuda_ext" .
    ln -s /home/datasets/ImageNet/train .
    ln -s /home/datasets/ImageNet/val .
    python main_amp.py -a resnet50 --b 224 --workers 4 --opt-level O3 ./
    cd /home/jeff/work/wandb/thirdparty/nvidia-apex/examples/imagenet

