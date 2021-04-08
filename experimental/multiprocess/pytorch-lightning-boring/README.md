pyenv virtualenv 3.6.8 ptl1
pyenv shell ptl1

pip install -r requirements.txt
# alternatively use this for cuda 10.1
# pip install -r requirements_cu101.txt

./train.py --acc=ddp_cpu --num_processes=2
# problem with wandb: hangs at end, two run headers
# ./train.py --acc=ddp_cpu --num_processes=2 --use_wandb

./train.py --acc=ddp_spawn --gpus=2
# problem with wandb: hangs at end, two run headers
# ./train.py --acc=ddp_spawn --gpus=2 --use_wandb

./train.py --acc=ddp --gpus=2
# problem with wandb: file not found (chdir somewhere in logger?)
# ./train.py --acc=ddp --gpus=2 --use_wandb

./train.py --acc=dp --gpus=2
# works fine with wandb
./train.py --acc=dp --gpus=2 --use_wandb

# does not work even without wandb
# ./train.py --acc=ddp2 --gpus=2
