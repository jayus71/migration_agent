import os
import argparse
import random
import string
from typing import List, Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from torchvision.models import resnet50

# ----------------------------------------------------------------------
# Constants from DJL CaptchaDataset
# ----------------------------------------------------------------------
IMAGE_HEIGHT = 60
IMAGE_WIDTH = 160
CAPTCHA_LENGTH = 6
CAPTCHA_OPTIONS = 12

# 12 possible characters (digits + A, B)
CAPTCHA_CHARS = string.digits + "AB"  # "0123456789AB"
assert len(CAPTCHA_CHARS) == CAPTCHA_OPTIONS


# ----------------------------------------------------------------------
# Model: ResNet50 followed by reshape/split into 6 digit predictions
# ----------------------------------------------------------------------
class CaptchaModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.resnet = resnet50(pretrained=False, num_classes=CAPTCHA_OPTIONS * CAPTCHA_LENGTH)

    def forward(self, x):
        x = self.resnet(x)                                  # [B, 72]
        x = x.view(x.size(0), CAPTCHA_LENGTH, CAPTCHA_OPTIONS)  # [B, 6, 12]
        return [x[:, i, :] for i in range(CAPTCHA_LENGTH)]   # list of 6 × [B, 12]


# ----------------------------------------------------------------------
# Loss: sum of 6 softmax cross-entropy losses (one per digit)
# ----------------------------------------------------------------------
def captcha_loss(outputs, labels):
    total = 0.0
    for i in range(CAPTCHA_LENGTH):
        total = total + F.cross_entropy(outputs[i], labels[i])
    return total


# ----------------------------------------------------------------------
# Synthetic Captcha Dataset (mimics DJL CaptchaDataset)
# ----------------------------------------------------------------------
class CaptchaDataset(Dataset):
    def __init__(self, size=1000, usage='train', transform=None):
        self.size = size
        self.usage = usage
        self.transform = transform
        self.labels = []
        for _ in range(size):
            self.labels.append([random.randint(0, CAPTCHA_OPTIONS - 1) for _ in range(CAPTCHA_LENGTH)])

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        labels = self.labels[idx]
        img = self._generate_image(labels)
        if self.transform:
            img = self.transform(img)
        return img, labels

    def _generate_image(self, labels):
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('L', (IMAGE_WIDTH, IMAGE_HEIGHT), color=255)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except Exception:
            font = ImageFont.load_default()
        for i, label in enumerate(labels):
            char = CAPTCHA_CHARS[label]
            x = 20 + i * 20
            y = random.randint(5, 15)
            draw.text((x, y), char, fill=0, font=font)
        # Add some noise
        for _ in range(100):
            x = random.randint(0, IMAGE_WIDTH - 1)
            y = random.randint(0, IMAGE_HEIGHT - 1)
            draw.point((x, y), fill=0)
        return img


def collate_fn(batch):
    imgs = torch.stack([item[0] for item in batch])
    labels = [torch.tensor([item[1][i] for item in batch], dtype=torch.long)
              for i in range(CAPTCHA_LENGTH)]
    return imgs, labels


# ----------------------------------------------------------------------
# Interface wrapper for build_training(context)
# ----------------------------------------------------------------------
class TrainingContextWrapper:
    def __init__(self, context):
        self.context = context
        self.device = torch.device('cpu')
        self.model = CaptchaModel().to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.optimizer.zero_grad()

    def parameters(self):
        return list(self.model.parameters())

    def buffers(self):
        return list(self.model.buffers())

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        if isinstance(inputs, (list, tuple)):
            x = inputs[0]
        else:
            x = inputs
        x = x.to(self.device)
        outputs = self.model(x)
        return [o for o in outputs]

    def loss(self, outputs, labels):
        return captcha_loss(outputs, labels)

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()

    def optimizer_state(self):
        state_list = []
        for p in self.parameters():
            if p in self.optimizer.state:
                st = self.optimizer.state[p]
                updates = int(st['step'].item()) if 'step' in st else 0
                d = {'updates': updates}
                if 'exp_avg' in st:
                    d['means'] = st['exp_avg']
                if 'exp_avg_sq' in st:
                    d['variances'] = st['exp_avg_sq']
                state_list.append(d)
            else:
                state_list.append({'updates': 0})
        return state_list


def build_training(context):
    return TrainingContextWrapper(context)


# ----------------------------------------------------------------------
# Main training program
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='Train CAPTCHA model (DJL TrainCaptcha translation)')
    parser.add_argument('--epoch', type=int, default=10, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--output-dir', type=str, default='build', help='Output directory for checkpoints')
    parser.add_argument('--limit', type=int, default=-1, help='Limit number of samples (-1 for all)')
    parser.add_argument('--max-gpus', type=int, default=-1, help='Max GPUs to use (-1 for all, 0 for CPU)')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])

    train_size = 1000 if args.limit == -1 else args.limit
    val_size = 200 if args.limit == -1 else max(1, args.limit // 5)

    train_dataset = CaptchaDataset(size=train_size, usage='train', transform=transform)
    val_dataset = CaptchaDataset(size=val_size, usage='validation', transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True,
                              collate_fn=collate_fn, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False,
                            collate_fn=collate_fn, num_workers=0)

    device = torch.device('cuda' if args.max_gpus != 0 and torch.cuda.is_available() else 'cpu')
    model = CaptchaModel().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    best_val_loss = float('inf')

    for epoch in range(args.epoch):
        model.train()
        train_loss = 0.0
        for imgs, labels in train_loader:
            imgs = imgs.to(device)
            labels = [l.to(device) for l in labels]
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = captcha_loss(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        avg_train_loss = train_loss / len(train_loader)

        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs = imgs.to(device)
                labels = [l.to(device) for l in labels]
                outputs = model(imgs)
                loss = captcha_loss(outputs, labels)
                val_loss += loss.item()
                for i in range(CAPTCHA_LENGTH):
                    preds = outputs[i].argmax(dim=1)
                    correct += (preds == labels[i]).sum().item()
                    total += labels[i].size(0)
        avg_val_loss = val_loss / len(val_loader) if len(val_loader) > 0 else 0.0
        acc = correct / (total * CAPTCHA_LENGTH) if total > 0 else 0.0

        print(f"Epoch {epoch + 1}/{args.epoch} - Train Loss: {avg_train_loss:.4f}, "
              f"Val Loss: {avg_val_loss:.4f}, Acc: {acc:.4f}")

        # Save best model checkpoint
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), os.path.join(args.output_dir, 'best_model.pt'))
            with open(os.path.join(args.output_dir, 'model.properties'), 'w') as f:
                f.write(f"Accuracy={acc:.5f}\n")
                f.write(f"Loss={avg_val_loss:.5f}\n")

    # Save final model
    torch.save(model.state_dict(), os.path.join(args.output_dir, 'final_model.pt'))
    print("Training complete. Models saved to", args.output_dir)


if __name__ == '__main__':
    main()
