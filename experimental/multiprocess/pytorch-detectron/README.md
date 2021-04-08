https://github.com/wandb/client/issues/1720

Get spacenet dataset and put in directory `spacenet`

jupyter nbconvert --to script Spacenet.ipynb
mv Spacenet.txt Spacenet.py

# reproduce problem in wandb<=0.10.23
WANDB_CONSOLE=wrap ./detectron-spacenet.py
