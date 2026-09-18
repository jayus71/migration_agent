import os
import argparse
import torch
import torch.nn as nn
import torch.optim as optim


class MLP(nn.Module):
    def __init__(self):
        super(MLP, self).__init__()
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 10)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.relu(x)
        x = self.fc3(x)
        return x


class TrainingContext:
    def __init__(self, model, loss_fn, optimizer):
        self.model = model
        self.loss_fn = loss_fn
        self.optimizer = optimizer

    def parameters(self):
        return list(self.model.parameters())

    def buffers(self):
        return list(self.model.buffers())

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        x = inputs[0]
        out = self.model(x)
        return [out]

    def loss(self, outputs, labels):
        return self.loss_fn(outputs[0], labels[0])

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()

    def optimizer_state(self):
        states = []
        for param in self.model.parameters():
            state = self.optimizer.state.get(param, {})
            if not state:
                states.append({
                    'updates': 0,
                    'means': torch.zeros_like(param),
                    'variances': torch.zeros_like(param)
                })
            else:
                step = state['step']
                if isinstance(step, torch.Tensor):
                    step = int(step.item())
                states.append({
                    'updates': step,
                    'means': state['exp_avg'],
                    'variances': state['exp_avg_sq']
                })
        return states


def build_training(context):
    model = MLP()
    model = model.to(torch.float32)
    model = model.cpu()
    loss_fn = nn.CrossEntropyLoss()
    optimizer = optim.Adam(
        model.parameters(),
        lr=0.001,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0
    )
    return TrainingContext(model, loss_fn, optimizer)


def main():
    import torchvision
    from torchvision import transforms, datasets
    from torch.utils.data import DataLoader

    parser = argparse.ArgumentParser(description='Train MLP on MNIST')
    parser.add_argument('--epoch', type=int, default=10, help='number of epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='batch size')
    parser.add_argument('--limit', type=int, default=0, help='limit number of samples per dataset (0 for no limit)')
    parser.add_argument('--max-gpus', type=int, default=-1, help='max GPUs to use (-1 for all, 0 for CPU)')
    parser.add_argument('--output-dir', type=str, default='build/model', help='output directory for checkpoints')
    args = parser.parse_args()

    if args.max_gpus == 0:
        device = torch.device('cpu')
    else:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    transform = transforms.ToTensor()
    train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(root='./data', train=False, download=True, transform=transform)

    if args.limit > 0:
        train_dataset = torch.utils.data.Subset(train_dataset, range(min(len(train_dataset), args.limit)))
        test_dataset = torch.utils.data.Subset(test_dataset, range(min(len(test_dataset), args.limit)))

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=True)

    model = MLP().to(device)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = optim.Adam(
        model.parameters(),
        lr=0.001,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0
    )

    os.makedirs(args.output_dir, exist_ok=True)

    for epoch in range(1, args.epoch + 1):
        model.train()
        for data, target in train_loader:
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = loss_fn(output, target)
            loss.backward()
            optimizer.step()

        model.eval()
        correct = 0
        total = 0
        val_loss = 0.0
        with torch.no_grad():
            for data, target in test_loader:
                data, target = data.to(device), target.to(device)
                output = model(data)
                val_loss += loss_fn(output, target).item() * data.size(0)
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                total += data.size(0)

        val_loss /= total
        accuracy = correct / total
        print(f'Epoch {epoch}: Val Loss: {val_loss:.5f}, Accuracy: {accuracy:.5f}')

        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'accuracy': accuracy,
            'loss': val_loss,
        }
        torch.save(checkpoint, os.path.join(args.output_dir, f'model-{epoch}.pt'))
        torch.save(checkpoint, os.path.join(args.output_dir, 'model.pt'))


if __name__ == '__main__':
    main()
