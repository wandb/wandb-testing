def run():
    import wandb
    wandb.init()


if __name__ == "__main__":
    import multiprocessing as mp
    p = mp.Process(target=run)
    p.start()
    p.join()
