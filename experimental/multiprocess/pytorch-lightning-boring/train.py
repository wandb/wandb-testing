#!/usr/bin/env python
import argparse
import os

import torch
from torch.utils.data import DataLoader, Dataset

import pytorch_lightning as pl
from pytorch_lightning import LightningModule
from pytorch_lightning.loggers import WandbLogger


class RandomDataset(Dataset):
    def __init__(self, size, num_samples):
        self.len = num_samples
        self.data = torch.randn(num_samples, size)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return self.len


class BoringModel(LightningModule):

    def __init__(self):
        super().__init__()
        self.layer = torch.nn.Linear(32, 2)

    def forward(self, x):
        return self.layer(x)

    def loss(self, batch, prediction):
        return torch.nn.functional.mse_loss(prediction, torch.ones_like(prediction))

    def training_step(self, batch, batch_idx):
        output = self.layer(batch)
        loss = self.loss(batch, output)
        self.log('train_loss', loss, sync_dist=True)
        return loss

    def validation_step(self, batch, batch_idx):
        output = self.layer(batch)
        loss = self.loss(batch, output)
        self.log('valid_loss', loss, sync_dist=True)

    def test_step(self, batch, batch_idx):
        output = self.layer(batch)
        loss = self.loss(batch, output)
        self.log('test_loss', loss, sync_dist=True)

    def configure_optimizers(self):
        return torch.optim.SGD(self.layer.parameters(), lr=0.01)


def main():

    acc_choices = ("ddp", "ddp_cpu", "ddp_spawn", "dp", "ddp2")
    parser = argparse.ArgumentParser()
    use_wandb = os.environ.get("USE_WANDB", "false")[:1] in ("1", "t", "T")
    parser.add_argument("--use_wandb",  action="store_true", default=use_wandb)
    parser.add_argument("--accelerator", choices=acc_choices)
    parser.add_argument("--max_epochs", default=3)
    parser.add_argument("--gpus", type=int)
    parser.add_argument("--num_processes", type=int, default=1)
    parser.add_argument("--num_nodes", type=int, default=1)
    parser.add_argument("--num_workers", type=int, default=0)
    args = parser.parse_args()

    # Set up data
    num_samples = 10000
    train = RandomDataset(32, num_samples)
    train = DataLoader(train, batch_size=32, num_workers=args.num_workers)
    val = RandomDataset(32, num_samples)
    val = DataLoader(val, batch_size=32, num_workers=args.num_workers)
    test = RandomDataset(32, num_samples)
    test = DataLoader(test, batch_size=32, num_workers=args.num_workers)
    
    # init model
    model = BoringModel()

    # set up wandb
    wandb_logger = WandbLogger()

    # Initialize a trainer
    trainer = pl.Trainer(
        max_epochs=args.max_epochs,
        num_processes=args.num_processes,
        num_nodes=args.num_nodes,
        gpus=args.gpus,
        accelerator=args.accelerator,
        logger=wandb_logger if args.use_wandb else None,
    )

    # Train the model
    trainer.fit(model, train, val)
    trainer.test(test_dataloaders=test)


if __name__ == "__main__":
    main()
