import argparse
import logging
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CIFAR10_MEAN = (0.4914, 0.4822, 0.4465)
CIFAR10_STD = (0.2023, 0.1994, 0.2010)


class Bottleneck(nn.Module):
    def __init__(self, in_ch, bottleneck_ch, out_ch, stride=1, downsample=None):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch, bottleneck_ch, kernel_size=1, stride=stride, bias=True)
        self.bn1 = nn.BatchNorm2d(bottleneck_ch)
        self.conv2 = nn.Conv2d(bottleneck_ch, bottleneck_ch, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(bottleneck_ch)
        self.conv3 = nn.Conv2d(bottleneck_ch, out_ch, kernel_size=1, bias=True)
        self.bn3 = nn.BatchNorm2d(out_ch)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out


class ResNetV1CIFAR(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.layer1 = self._make_layer(64, 64, 256, 3, stride=1)
        self.layer2 = self._make_layer(256, 128, 512, 4, stride=2)
        self.layer3 = self._make_layer(512, 256, 1024, 6, stride=2)
        self.layer4 = self._make_layer(1024, 512, 2048, 3, stride=2)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(2048, num_classes)

    def _make_layer(self, in_ch, bottleneck_ch, out_ch, blocks, stride):
        downsample = None
        if stride != 1 or in_ch != out_ch:
            downsample = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_ch)
            )
        layers = []
        layers.append(Bottleneck(in_ch, bottleneck_ch, out_ch, stride, downsample))
        for _ in range(1, blocks):
            layers.append(Bottleneck(out_ch, bottleneck_ch, out_ch, stride=1, downsample=None))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        return x


class TrainingWrapper:
    def __init__(self):
        self.model = ResNetV1CIFAR()
        self.model.float()
        self.model.cpu()
        self.model.train()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.CrossEntropyLoss()
        self._parameters = list(self.model.parameters())
        self._buffers = list(self.model.buffers())

    def parameters(self):
        return self._parameters

    def buffers(self):
        return self._buffers

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        x = inputs[0]
        logits = self.model(x)
        return [logits]

    def loss(self, outputs, labels):
        logits = outputs[0]
        target = labels[0].long()
        return self.criterion(logits, target)

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()

    def optimizer_state(self):
        states = []
        for p in self._parameters:
            state = self.optimizer.state.get(p, {})
            updates = state.get('step', 0)
            if isinstance(updates, torch.Tensor):
                updates = int(updates.item())
            else:
                updates = int(updates)
            d = {'updates': updates}
            if 'exp_avg' in state:
                d['means'] = state['exp_avg']
            else:
                d['means'] = torch.zeros_like(p)
            if 'exp_avg_sq' in state:
                d['variances'] = state['exp_avg_sq']
            else:
                d['variances'] = torch.zeros_like(p)
            states.append(d)
        return states


def build_training(context):
    return TrainingWrapper()


class Arguments:
    def __init__(self):
        self.epoch = 10
        self.batch_size = 32
        self.max_gpus = 1
        self.limit = -1
        self.output_dir = "build"
        self.pre_trained = False
        self.engine = "PyTorch"

    @staticmethod
    def parse_args(args=None):
        parser = argparse.ArgumentParser()
        parser.add_argument('--epoch', type=int, default=10)
        parser.add_argument('--batch-size', type=int, default=32)
        parser.add_argument('--max-gpus', type=int, default=1)
        parser.add_argument('--limit', type=int, default=-1)
        parser.add_argument('--output-dir', type=str, default='build')
        parser.add_argument('--pre-trained', action='store_true')
        parser.add_argument('--engine', type=str, default='PyTorch')
        parsed = parser.parse_args(args)
        a = Arguments()
        a.epoch = parsed.epoch
        a.batch_size = parsed.batch_size
        a.max_gpus = parsed.max_gpus
        a.limit = parsed.limit
        a.output_dir = parsed.output_dir
        a.pre_trained = parsed.pre_trained
        a.engine = parsed.engine
        return a


def get_model(arguments):
    if arguments.pre_trained:
        logger.warning("Pre-trained model loading is not supported in this translation. Using randomly initialized model.")
    model = ResNetV1CIFAR()
    return model


def get_dataset(usage, arguments):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD)
    ])
    if usage == 'train':
        dataset = datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
    else:
        dataset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
    if arguments.limit > 0:
        dataset = Subset(dataset, range(min(arguments.limit, len(dataset))))
    return dataset


def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    for inputs, labels in loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * inputs.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


def evaluate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


def test_saved_parameters(path, arguments):
    model = ResNetV1CIFAR()
    model_path = Path(path) / "resnetv1.pt"
    if not model_path.exists():
        logger.warning(f"Model file not found: {model_path}")
        return
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    device = torch.device('cpu')
    model.to(device)
    img_path = Path("src/test/resources/airplane1.png")
    if not img_path.exists():
        logger.warning(f"Test image not found: {img_path}")
        return
    img = Image.open(img_path).convert('RGB')
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD)
    ])
    img_tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(img_tensor)
        probs = F.softmax(logits, dim=1)
    top_probs, top_indices = probs.topk(3, dim=1)
    logger.info(f"Predict result: {list(zip(top_indices[0].tolist(), top_probs[0].tolist()))}")


def run_example(args):
    arguments = Arguments.parse_args(args)
    if arguments is None:
        return None
    model = get_model(arguments)
    device = torch.device('cuda' if torch.cuda.is_available() and arguments.max_gpus > 0 else 'cpu')
    model.to(device)
    train_dataset = get_dataset('train', arguments)
    val_dataset = get_dataset('test', arguments)
    train_loader = DataLoader(train_dataset, batch_size=arguments.batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=arguments.batch_size, shuffle=True, num_workers=2)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    for epoch in range(arguments.epoch):
        train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        logger.info(f"Epoch {epoch+1}/{arguments.epoch} - train loss: {train_loss:.4f}, train acc: {train_acc:.4f}, val loss: {val_loss:.4f}, val acc: {val_acc:.4f}")
    model_path = Path(arguments.output_dir) / "model"
    model_path.mkdir(parents=True, exist_ok=True)
    save_path = model_path / "resnetv1.pt"
    torch.save(model.state_dict(), save_path)
    test_saved_parameters(model_path, arguments)
    return model


if __name__ == '__main__':
    run_example(None)
