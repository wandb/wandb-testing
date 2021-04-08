pyenv virtualenv 3.6.8 pt1
pyenv shell pt1

pip install -r requirements.txt
# alternatively use this for cuda 10.1
# pip install -r requirements_cu101.txt

./train_mnist.py --distributed --num-epochs=2 --disable-wandb
# problem with wandb: hangs at end
./train_mnist.py --distributed --num-epochs=2
# fix for wandb
./train_mnist.py --distributed --num-epochs=2 --wandb-fix-finish
