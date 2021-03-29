#  ------------------------------------------------------------------------------------------
#  Copyright (c) Microsoft Corporation. All rights reserved.
#  Licensed under the MIT License (MIT). See LICENSE in the repo root for license information.
#  ------------------------------------------------------------------------------------------
import copy
import math
from unittest import mock
import numpy as np
import torch
from pytorch_lightning import Trainer

from InnerEye.SSL.byol.byol_module import BYOLInnerEye
from InnerEye.SSL.byol.byol_moving_average import BYOLMAWeightUpdate
from Tests.SSL.test_main import _get_dummy_val_train_rsna_dataloaders


def test_update_tau() -> None:
    byol_weight_update = BYOLMAWeightUpdate(initial_tau=0.99)
    trainer = Trainer()
    trainer.train_dataloader = _get_dummy_val_train_rsna_dataloaders()
    trainer.max_epochs = 5
    n_steps_per_epoch = len(trainer.train_dataloader)
    total_steps = n_steps_per_epoch * trainer.max_epochs
    byol_module = BYOLInnerEye(num_samples=16,
                               learning_rate=1e-3,
                               batch_size=4,
                               encoder_name="resnet50",
                               warmup_epochs=10)
    with mock.patch("InnerEye.SSL.byol.byol_module.BYOLInnerEye.global_step", 15):
        new_tau = byol_weight_update.update_tau(pl_module=byol_module, trainer=trainer)
    assert new_tau == 1 - 0.01 * (math.cos(math.pi * 15 / total_steps) + 1) / 2


def test_update_weights() -> None:
    online_network = torch.nn.Linear(in_features=3, out_features=1, bias=False)
    target_network = torch.nn.Linear(in_features=3, out_features=1, bias=False)
    byol_weight_update = BYOLMAWeightUpdate(initial_tau=0.9)
    old_target_net_weight = target_network.weight.data.numpy().copy()
    byol_weight_update.update_weights(online_network, target_network)
    assert np.isclose(target_network.weight.data.numpy(),
                      0.9 * old_target_net_weight + 0.1 * online_network.weight.data.numpy()).all()