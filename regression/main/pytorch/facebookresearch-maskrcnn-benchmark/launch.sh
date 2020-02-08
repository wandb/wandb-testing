wandb-docker-run -it -v /share/datasets/COCO/:/maskrcnn-benchmark/datasets/coco -v $PWD/wandb:/wandb jeffwandb/maskrcnn-benchmark2:latest /wandb/run.sh
