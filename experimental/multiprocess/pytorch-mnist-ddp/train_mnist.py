#!/usr/bin/env python
import argparse
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import wandb

import torch
import torch.distributed as dist
import torch.multiprocessing as mp
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.nn import DataParallel
from torch.optim.lr_scheduler import StepLR
from torch.utils.data.distributed import DistributedSampler
from torchvision import datasets, transforms


class MnistBasicNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output


class Monitor(object):
    def __init__(self, num_epochs, rank, world_size, use_wandb, distributed_mode):
        self.num_epochs = num_epochs
        self.rank = rank
        self.world_size = world_size
        self.use_wandb = use_wandb
        self.distributed_mode = distributed_mode
        self.reset()

    def log_batch(self, loss):
        if self.distributed_mode:
            dist.reduce(loss, 0, op=dist.ReduceOp.SUM)
            loss /= self.world_size
        loss = float(loss)
        self.loss_sum += loss
        self.loss_count += 1
        return loss

    def reset(self):
        self.loss_sum = 0
        self.loss_count = 0


class TrainMonitor(Monitor):
    def __init__(self, num_epochs, optimizer, rank, world_size, use_wandb, distributed_mode, skip_logs=20):
        super().__init__(num_epochs, rank, world_size, use_wandb, distributed_mode)
        self.optimizer = optimizer
        self.skip_logs = skip_logs

    def log_batch(self, epoch_idx, batch_idx, num_batches, loss):
        dist_loss = super().log_batch(loss)
        if self.rank == 0 and batch_idx % self.skip_logs == 0:
            log_str = '[{}/{}][{}/{}]\tLoss: {:.6f}'.format(epoch_idx, self.num_epochs, batch_idx, num_batches, dist_loss)
            print(log_str)

    def log_epoch(self, epoch_idx):
        if self.rank == 0:
            epoch_loss = self.loss_sum / self.loss_count
            log_str = f'Train Epoch: {epoch_idx}/{self.num_epochs} | avg loss: {epoch_loss:.6f}'
            print(log_str)

        if self.use_wandb:
            log_dict = {'train/loss': epoch_loss, 'train/lr_rate': self.optimizer.param_groups[0]['lr']}
            wandb.log(log_dict, step=epoch_idx)
        self.reset()


class ValMonitor(Monitor):
    def __init__(self, num_epochs, rank, world_size, use_wandb, distributed_mode):
        super().__init__(num_epochs, rank, world_size, use_wandb, distributed_mode)
        self.num_correct = 0
        self.epoch_samples = 0

    def log_batch(self, epoch_idx, batch_idx, loss, images, predictions, targets):
        super().log_batch(loss)
        images = torch.squeeze(images)
        predictions = torch.squeeze(predictions)
        targets = torch.squeeze(targets)

        if self.distributed_mode:
            im_list = [torch.ones_like(images) for _ in range(self.world_size)]
            pred_list = [torch.ones_like(predictions) for _ in range(self.world_size)]
            gt_list = [torch.ones_like(targets) for _ in range(self.world_size)]

            dist.all_gather(tensor=images, tensor_list=im_list)
            dist.all_gather(tensor=predictions, tensor_list=pred_list)
            dist.all_gather(tensor=targets, tensor_list=gt_list)
            if self.rank == 0:
                images = torch.cat(im_list, dim=0)
                predictions = torch.cat(pred_list, dim=0)
                targets = torch.cat(gt_list, dim=0)

        self.num_correct += int(predictions.eq(targets).sum())
        self.epoch_samples += int(targets.shape[0])

        # Visualize to wandb if this is the first batch of the epoch.
        if batch_idx == 1:
            if self.rank == 0:
                batch_size, _, _  = images.shape
                indices = np.random.choice(range(batch_size), 8)
                image_sample = ((images[indices, :, :].cpu().numpy() + 1) * 127.5).astype(np.uint8)
                pred_sample = predictions[indices].cpu().numpy()
                gt_sample = targets[indices].cpu().numpy()
                hsep = 127 * np.ones((28, 1), dtype=np.uint8)
                vis_image = np.hstack([np.hstack((im, hsep)) for im in image_sample])[:, :-1]
                caption = 'GT: ' + ' '.join([str(x) for x in gt_sample]) + ', Pred: ' + ' '.join([str(x) for x in pred_sample])
            if self.use_wandb:
                summary_dict = {"val_examples": wandb.Image(vis_image, caption=caption)}
                wandb.log(summary_dict, step=epoch_idx)

    def log_epoch(self, epoch_idx):
        if self.rank == 0:
            epoch_loss = self.loss_sum / self.loss_count
            epoch_acc = self.num_correct / self.epoch_samples
            log_str = f'Val Epoch {epoch_idx}/{self.num_epochs} | avg loss: {epoch_loss:.6f}, acc: {epoch_acc:.3f}'
            print(log_str)

        if self.use_wandb:
            wandb.log({'val/loss': epoch_loss, 'val/acc': epoch_acc}, step=epoch_idx)

        self.reset()
        self.num_correct = 0
        self.epoch_samples = 0


# Normalize to range from [0, 1] to [-1.0, +1.0].
def range_norm(x):
    return x*2-1


def distributed_train(batch_size, seed, lr, gamma, num_epochs, disable_wandb, wandb_fix_finish):
    num_gpus = torch.cuda.device_count()
    mp.spawn(
        primitive_train,
        nprocs=num_gpus,
        args=(num_gpus, batch_size, seed, lr, gamma, num_epochs, disable_wandb, True, wandb_fix_finish), join=True
    )
    return 0


def primitive_train(rank, world_size, batch_size, seed, lr, gamma, num_epochs, disable_wandb, distributed_mode=False, wandb_fix_finish=False):
   # Capture function arguments in a dict.
    config_dict = vars()

    def setup(rank, world_size):
        os.environ['MASTER_ADDR'] = 'localhost'
        os.environ['MASTER_PORT'] = '12355'
        # initialize the process group
        dist.init_process_group("nccl", rank=rank, world_size=world_size)

    def cleanup():
        dist.destroy_process_group()

    # Disable wandb or only run on rank 0 if DDP.
    use_wandb = not disable_wandb and (not distributed_mode or rank == 0)

    if distributed_mode:
        setup(rank, world_size)

    assert(torch.cuda.is_available())
    assert(torch.cuda.device_count() > 1)

    torch.manual_seed(seed)
    device = torch.device(f'cuda:{rank}' if distributed_mode else 'cuda')

    transform = transforms.Compose([transforms.ToTensor(), range_norm])
    train_dset = datasets.FashionMNIST('./mnist', train=True, download=True, transform=transform)
    val_dset = datasets.FashionMNIST('./mnist', train=False, transform=transform)

    dataloader_kwargs = {'batch_size': batch_size, 'num_workers': 1, 'pin_memory': True}
    tdl_kwargs = {**dataloader_kwargs}
    vdl_kwargs = {**dataloader_kwargs}
    if distributed_mode:
        tdl_kwargs['sampler'] = DistributedSampler(train_dset, num_replicas=world_size, rank=rank)
        vdl_kwargs['sampler'] = DistributedSampler(val_dset, num_replicas=world_size, rank=rank)
    else:
        tdl_kwargs['shuffle'] = True
        vdl_kwargs['shuffle'] = True

    train_loader = torch.utils.data.DataLoader(train_dset, **tdl_kwargs)
    val_loader = torch.utils.data.DataLoader(val_dset, **vdl_kwargs)

    model = MnistBasicNet().to(device)
    if distributed_mode:
        model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[rank])
    else:
        model = DataParallel(model, list(range(torch.cuda.device_count())))

    optimizer = optim.Adadelta(model.parameters(), lr=lr)

    train_monitor = TrainMonitor(num_epochs, optimizer, rank, world_size, use_wandb, distributed_mode)
    val_monitor = ValMonitor(num_epochs, rank, world_size, use_wandb, distributed_mode)

    if use_wandb:
        wandb_dir = Path("./wandb")
        wandb_dir.mkdir(exist_ok=True, parents=True)
        wandb.init(
            name=datetime.now().strftime("%Y%m%d-%H%M%S") + "_train",
            resume=False,
            dir=str(wandb_dir),
            config=dict(config_dict))
        wandb.watch(model)

    scheduler = StepLR(optimizer, step_size=1, gamma=gamma)
    for epoch_idx in range(1, num_epochs + 1):
        train_epoch(model, train_loader, optimizer, epoch_idx, train_monitor)
        val_epoch(model, val_loader, epoch_idx, val_monitor)
        scheduler.step()

    if distributed_mode:
        m = model.module
    else:
        m = model
    torch.save(m.state_dict(), "mnist_cnn.pt")

    if use_wandb:
        wandb.save("mnist_cnn.pt")

    if distributed_mode:
        if wandb_fix_finish:
            if rank == 0:
                wandb.finish()
        cleanup()


def train_epoch(model, train_loader, optimizer, epoch_idx, monitor):
    device = next(model.parameters()).device

    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        monitor.log_batch(epoch_idx, batch_idx, len(train_loader), loss.detach())
    monitor.log_epoch(epoch_idx)


def val_epoch(model, val_loader, epoch_idx, monitor):
    device = next(model.parameters()).device
    model.eval()
    with torch.no_grad():
        for batch_idx, (data, target) in enumerate(val_loader):
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss = F.nll_loss(output, target, reduction='mean')
            pred = output.argmax(dim=1, keepdim=True)
            monitor.log_batch(epoch_idx, batch_idx, loss.detach(), data.detach(), pred.detach(), target.detach())
    monitor.log_epoch(epoch_idx)


def main():
    # Training hyperparameters.
    parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
    parser.add_argument('--batch-size', type=int, default=256, help='input batch size for training')
    parser.add_argument('--num-epochs', type=int, default=10, help='number of epochs to train')
    parser.add_argument('--lr', type=float, default=0.5, help='learning rate')
    parser.add_argument('--gamma', type=float, default=0.7, help='Learning rate step gamma')
    parser.add_argument('--seed', type=int, default=42, help='random seed')
    parser.add_argument('--distributed', action='store_true', default=False)
    parser.add_argument('--disable-wandb', action='store_true', default=False)
    parser.add_argument('--wandb-fix-finish', action='store_true', default=False)
    args = parser.parse_args()

    if args.distributed:
        distributed_train(args.batch_size, args.seed, args.lr, args.gamma, args.num_epochs, args.disable_wandb, wandb_fix_finish=args.wandb_fix_finish)
    else:
        primitive_train(0, 0, args.batch_size, args.seed, args.lr, args.gamma, args.num_epochs, args.disable_wandb)


if __name__ == '__main__':
    main()
