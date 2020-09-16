ulimit -n 4096
./regression.py --spec ::~broken --cli_base wandb --cli_repo wandb/client-ng.git $* main/
