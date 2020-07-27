ulimit -n 4096
./regression.py --spec ::~broken --cli_base wandb-ng --cli_repo wandb/client-ng.git $* main/
