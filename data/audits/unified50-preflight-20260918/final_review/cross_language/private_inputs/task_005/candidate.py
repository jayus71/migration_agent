import argparse
import math
import os
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import numpy as np
import torchvision.transforms as T


# ----------------------------------------------------------------------
# Model architecture: Single Shot Detection (SSD)
# ----------------------------------------------------------------------
class DownSamplingBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool(x)
        return x


class SingleShotDetection(nn.Module):
    def __init__(self, num_classes=1, num_features=3):
        super().__init__()
        self.num_classes = num_classes

        # Base network: 3 downsampling blocks
        self.base = nn.Sequential(
            DownSamplingBlock(3, 16),
            DownSamplingBlock(16, 32),
            DownSamplingBlock(32, 64),
        )

        # Extra downsampling blocks
        self.extra_blocks = nn.ModuleList()
        in_ch = 64
        for _ in range(num_features):
            self.extra_blocks.append(DownSamplingBlock(in_ch, 128))
            in_ch = 128

        # Feature channels: base output (64), extra blocks (128 each), global pool (128)
        feature_channels = [64] + [128] * (num_features + 1)
        num_anchors = 4
        class_out = num_anchors * (num_classes + 1)
        box_out = num_anchors * 4

        self.class_preds = nn.ModuleList()
        self.box_preds = nn.ModuleList()
        for ch in feature_channels:
            self.class_preds.append(nn.Conv2d(ch, class_out, kernel_size=3, padding=1))
            self.box_preds.append(nn.Conv2d(ch, box_out, kernel_size=3, padding=1))

        # Anchor generation
        sizes = [
            [0.2, 0.272],
            [0.37, 0.447],
            [0.54, 0.619],
            [0.71, 0.79],
            [0.88, 0.961],
        ]
        ratios = [[1.0, 2.0, 0.5]] * len(sizes)
        feature_map_sizes = [32, 16, 8, 4, 1]
        self.anchors = self._generate_anchors(sizes, ratios, feature_map_sizes)

    def _generate_anchors(self, sizes, ratios, feature_map_sizes):
        anchors = []
        for k, f in enumerate(feature_map_sizes):
            s_min, s_max = sizes[k]
            for i in range(f):
                for j in range(f):
                    cx = (j + 0.5) / f
                    cy = (i + 0.5) / f
                    for ratio in ratios[k]:
                        if ratio == 1.0:
                            for size in [s_min, s_max]:
                                w = size * math.sqrt(ratio)
                                h = size / math.sqrt(ratio)
                                anchors.append([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2])
                        else:
                            size = s_min
                            w = size * math.sqrt(ratio)
                            h = size / math.sqrt(ratio)
                            anchors.append([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2])
        return torch.tensor(anchors, dtype=torch.float32)

    def forward(self, x):
        features = []
        out = self.base(x)
        features.append(out)

        for block in self.extra_blocks:
            out = block(out)
            features.append(out)

        # Global average pooling on the last feature map
        pooled = out.mean(dim=[2, 3], keepdim=True)
        features.append(pooled)

        class_preds = []
        box_preds = []
        for i, feat in enumerate(features):
            N, C, H, W = feat.shape
            cp = self.class_preds[i](feat)
            cp = cp.permute(0, 2, 3, 1).reshape(N, -1, self.num_classes + 1)
            class_preds.append(cp)

            bp = self.box_preds[i](feat)
            bp = bp.permute(0, 2, 3, 1).reshape(N, -1, 4)
            box_preds.append(bp)

        class_pred = torch.cat(class_preds, dim=1)
        box_pred = torch.cat(box_preds, dim=1).reshape(N, -1)
        anchors = self.anchors.unsqueeze(0).expand(N, -1, -1)
        return anchors, class_pred, box_pred


# ----------------------------------------------------------------------
# Loss: Single Shot Detection Loss
# ----------------------------------------------------------------------
def ssd_loss(
    class_pred,
    box_pred,
    anchors,
    labels,
    alpha=1.0,
    neg_ratio=3,
    neg_thresh=0.5,
    overlap_thresh=0.5,
):
    N = class_pred.shape[0]
    num_anchors = class_pred.shape[1]
    num_classes = class_pred.shape[2] - 1
    box_pred = box_pred.reshape(N, num_anchors, 4)
    anchors = anchors.reshape(num_anchors, 4)

    total_loss = 0.0
    for i in range(N):
        gt = labels[i]
        gt_boxes = gt[:, 1:5]
        gt_classes = gt[:, 0].long()
        num_objects = gt_boxes.shape[0]

        # IoU between anchors and ground truth boxes
        anchors_exp = anchors.unsqueeze(1)  # (num_anchors, 1, 4)
        gt_exp = gt_boxes.unsqueeze(0)      # (1, num_objects, 4)
        inter_xmin = torch.max(anchors_exp[..., 0], gt_exp[..., 0])
        inter_ymin = torch.max(anchors_exp[..., 1], gt_exp[..., 1])
        inter_xmax = torch.min(anchors_exp[..., 2], gt_exp[..., 2])
        inter_ymax = torch.min(anchors_exp[..., 3], gt_exp[..., 3])
        inter_w = (inter_xmax - inter_xmin).clamp(min=0)
        inter_h = (inter_ymax - inter_ymin).clamp(min=0)
        inter_area = inter_w * inter_h

        anchor_area = (anchors[:, 2] - anchors[:, 0]) * (anchors[:, 3] - anchors[:, 1])
        gt_area = (gt_boxes[:, 2] - gt_boxes[:, 0]) * (gt_boxes[:, 3] - gt_boxes[:, 1])
        union_area = anchor_area.unsqueeze(1) + gt_area.unsqueeze(0) - inter_area
        iou = inter_area / union_area

        best_iou, best_gt_idx = iou.max(dim=1)
        best_anchor_iou, best_anchor_idx = iou.max(dim=0)

        matches = best_gt_idx.clone()
        matches[best_iou < overlap_thresh] = -1
        for j in range(num_objects):
            matches[best_anchor_idx[j]] = j

        pos_mask = matches >= 0
        target_classes = torch.zeros(num_anchors, dtype=torch.long, device=class_pred.device)
        safe_matches = matches.clamp(min=0)
        matched_classes = gt_classes[safe_matches]
        target_classes[pos_mask] = matched_classes[pos_mask]

        matched_boxes = gt_boxes[safe_matches]
        anchor_cx = (anchors[:, 0] + anchors[:, 2]) / 2
        anchor_cy = (anchors[:, 1] + anchors[:, 3]) / 2
        anchor_w = anchors[:, 2] - anchors[:, 0]
        anchor_h = anchors[:, 3] - anchors[:, 1]

        matched_cx = (matched_boxes[:, 0] + matched_boxes[:, 2]) / 2
        matched_cy = (matched_boxes[:, 1] + matched_boxes[:, 3]) / 2
        matched_w = matched_boxes[:, 2] - matched_boxes[:, 0]
        matched_h = matched_boxes[:, 3] - matched_boxes[:, 1]

        target_offsets = torch.zeros(num_anchors, 4, device=class_pred.device)
        dx = (matched_cx - anchor_cx) / anchor_w
        dy = (matched_cy - anchor_cy) / anchor_h
        dw = torch.log(matched_w / anchor_w)
        dh = torch.log(matched_h / anchor_h)
        offsets = torch.stack([dx, dy, dw, dh], dim=1)
        target_offsets[pos_mask] = offsets[pos_mask]

        ce_loss = -F.log_softmax(class_pred[i], dim=1)
        ce_loss = ce_loss.gather(1, target_classes.unsqueeze(1)).squeeze(1)

        num_pos = pos_mask.sum().item()
        if num_pos == 0:
            num_pos = 1
            cls_loss = ce_loss.mean()
            loc_loss = 0.0
        else:
            neg_loss = ce_loss[~pos_mask]
            neg_loss = neg_loss[neg_loss > neg_thresh]
            num_neg = min(neg_ratio * num_pos, neg_loss.shape[0])
            if num_neg > 0:
                neg_loss_sorted, _ = torch.topk(neg_loss, num_neg)
                neg_loss_sum = neg_loss_sorted.sum()
            else:
                neg_loss_sum = 0.0
            pos_loss_sum = ce_loss[pos_mask].sum()
            cls_loss = (pos_loss_sum + neg_loss_sum) / num_pos

            diff = box_pred[i] - target_offsets
            abs_diff = diff.abs()
            smooth_l1 = torch.where(abs_diff < 1, 0.5 * diff * diff, abs_diff - 0.5)
            loc_loss = smooth_l1[pos_mask].sum() / num_pos

        total_loss += cls_loss + alpha * loc_loss

    return total_loss / N


# ----------------------------------------------------------------------
# Trainer wrapper for the common interface
# ----------------------------------------------------------------------
class TrainerWrapper:
    def __init__(self, model, optimizer):
        self.model = model
        self.optimizer = optimizer

    def parameters(self):
        return list(self.model.parameters())

    def buffers(self):
        return [b for name, b in self.model.named_buffers() if "num_batches_tracked" not in name]

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels=None):
        x = inputs[0]
        anchors, class_pred, box_pred = self.model(x)
        return [anchors, class_pred, box_pred]

    def loss(self, outputs, labels):
        anchors, class_pred, box_pred = outputs
        label_tensor = labels[0]
        return ssd_loss(class_pred, box_pred, anchors, label_tensor)

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()

    def optimizer_state(self):
        param_list = self.parameters()
        state = []
        for p in param_list:
            if p in self.optimizer.state:
                s = self.optimizer.state[p]
                d = {
                    "updates": s["step"].item() if isinstance(s["step"], torch.Tensor) else s["step"],
                    "means": s["exp_avg"],
                    "variances": s["exp_avg_sq"],
                }
            else:
                d = {"updates": 0, "means": None, "variances": None}
            state.append(d)
        return state


def build_training(context):
    model = SingleShotDetection(num_classes=1, num_features=3)
    optimizer = optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8)
    return TrainerWrapper(model, optimizer)


# ----------------------------------------------------------------------
# Dataset helper (placeholder for PikachuDetection)
# ----------------------------------------------------------------------
class PikachuDetection(Dataset):
    """
    Minimal placeholder for DJL's PikachuDetection.
    Expects the dataset to be already downloaded and extracted.
    Replace this with a full implementation if the dataset is available.
    """
    def __init__(self, usage="train", limit=0, transform=None):
        self.usage = usage
        self.limit = limit
        self.transform = transform
        # In a real translation, this would load the Pikachu dataset from disk.
        # For now, raise an informative error if used.
        raise NotImplementedError(
            "PikachuDetection dataset loading is not implemented in this translation. "
            "Please provide the dataset or use build_training for paired testing."
        )

    def __len__(self):
        return 0

    def __getitem__(self, idx):
        raise NotImplementedError


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Train Pikachu SSD example")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--epoch", type=int, default=10, help="Number of epochs")
    parser.add_argument("--limit", type=int, default=0, help="Limit dataset size")
    parser.add_argument("--max-gpus", type=int, default=-1, help="Max GPUs to use")
    parser.add_argument("--output-dir", type=str, default="build/pikachu", help="Output directory")
    args = parser.parse_args()

    # The original Java example uses DJL's EasyTrain.fit with PikachuDetection.
    # Since the dataset is not bundled, we only show the training configuration.
    print("Pikachu SSD training configuration:")
    print(f"  batch_size = {args.batch_size}")
    print(f"  epoch      = {args.epoch}")
    print(f"  limit      = {args.limit}")
    print(f"  max_gpus   = {args.max_gpus}")
    print(f"  output_dir = {args.output_dir}")
    print("Dataset loading is not implemented in this translation.")


if __name__ == "__main__":
    main()
