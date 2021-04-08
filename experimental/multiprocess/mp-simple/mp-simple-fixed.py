def run():
    import wandb
    try:
        wandb.init()
    finally:
        wandb.finish()


if __name__ == "__main__":
    import multiprocessing as mp
    p = mp.Process(target=run)
    p.start()
    p.join()
