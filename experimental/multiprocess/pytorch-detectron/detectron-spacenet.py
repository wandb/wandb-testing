#!/usr/bin/env python

# install dependencies: 
## !pip install pyyaml==5.1
import torch, torchvision
print(torch.__version__, torch.cuda.is_available())
## !gcc --version
# opencv is pre-installed on colab

# install detectron2: (Colab has CUDA 10.1 + torch 1.7)
# See https://detectron2.readthedocs.io/tutorials/install.html for instructions
import torch
assert torch.__version__.startswith("1.7")
## !pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu101/torch1.7/index.html
# exit(0)  # After installation, you need to "restart runtime" in Colab. This line can also restart runtime

import detectron2
from detectron2.utils.logger import setup_logger
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.data.datasets import register_coco_instances
from detectron2.utils.visualizer import Visualizer
from detectron2.engine import DefaultTrainer
from detectron2.config import get_cfg
from detectron2.utils.visualizer import ColorMode
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader
## from google.colab.patches import cv2_imshow
import random, cv2, os

## from google.colab import drive
## drive.mount('/content/drive')

## %cd drive/My Drive/data/
## %ls

# Data Directories
traindir = 'spacenet/'

# Register train and test datasets
register_coco_instances("train", {}, traindir + 'coco.json', traindir + 'images/')

# Generate metadata
train_metadata = MetadataCatalog.get("train")

# Get train and test dataset catalogs
train_dicts = DatasetCatalog.get("train")

# Display a random training image with annotations
d = random.sample(train_dicts, 1)
d = d[0]
img = cv2.imread(d["file_name"])
visualizer = Visualizer(img[:, :, ::-1], metadata=train_metadata, scale=1.0)
vis = visualizer.draw_dataset_dict(d)
print("filename = " + d['file_name'])
## cv2_imshow(vis.get_image()[:, :, ::-1])

## %pip install wandb

import wandb
wandb.login()
wandb.init(project='test4', sync_tensorboard=True)

# Train the network
cfg = get_cfg()
cfg.merge_from_file(
    model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
)
cfg.DATASETS.TRAIN = ("train",)
cfg.DATASETS.TEST = ()  # no metrics implemented for this dataset
cfg.DATALOADER.NUM_WORKERS = 2
cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")  # initialize from model zoo
cfg.SOLVER.IMS_PER_BATCH = 2
cfg.SOLVER.BASE_LR = 0.02
cfg.SOLVER.MAX_ITER = (
    300
)  # 300 iterations seems good enough, but you can certainly train longer
cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = (
    128
)  # faster, and good enough for this toy dataset
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 5  # 5 classes (tank, support_vehicle, trailer, other_afv, non_afv)

os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
trainer = DefaultTrainer(cfg)
trainer.resume_or_load(resume=False)
trainer.train()
