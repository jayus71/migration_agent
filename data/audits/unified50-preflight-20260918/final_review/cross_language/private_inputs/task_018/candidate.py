import os
import re
import math
import time
import random
import urllib.request
import collections

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader


class Vocab:
    def __init__(self, tokens=None, min_freq=0, reserved_tokens=None):
        if tokens is None:
            tokens = []
        if reserved_tokens is None:
            reserved_tokens = []
        reserved_tokens = ['<unk>'] + reserved_tokens
        counter = collections.Counter(tokens)
        self.idx_to_token = list(reserved_tokens)
        self.token_to_idx = {token: idx for idx, token in enumerate(self.idx_to_token)}
        for token, freq in counter.most_common():
            if freq < min_freq:
                break
            if token not in self.token_to_idx:
                self.token_to_idx[token] = len(self.idx_to_token)
                self.idx_to_token.append(token)
        self.unk = 0

    def __len__(self):
        return len(self.idx_to_token)

    def __getitem__(self, tokens):
        if not isinstance(tokens, (list, tuple)):
            return self.token_to_idx.get(tokens, self.unk)
        return [self.__getitem__(token) for token in tokens]

    def to_tokens(self, indices):
        if not isinstance(indices, (list, tuple)):
            return self.idx_to_token[indices]
        return [self.idx_to_token[index] for index in indices]


def download_time_machine():
    url = 'https://d2l-data.s3-accelerate.amazonaws.com/timemachine.txt'
    filename = 'timemachine.txt'
    if not os.path.exists(filename):
        urllib.request.urlretrieve(url, filename)
    return filename


def read_time_machine():
    filename = download_time_machine()
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return [re.sub('[^A-Za-z]+', ' ', line).strip().lower() for line in lines]


def tokenize(lines, token='char'):
    if token == 'word':
        return [line.split() for line in lines]
    elif token == 'char':
        return [list(line) for line in lines]
    else:
        raise ValueError('Unknown token type: ' + token)


def load_corpus_time_machine(max_tokens=-1):
    lines = read_time_machine()
    tokens = tokenize(lines, 'char')
    vocab = Vocab(tokens)
    corpus = [vocab[token] for line in tokens for token in line]
    if max_tokens > 0:
        corpus = corpus[:max_tokens]
    return corpus, vocab


class RNNModel(nn.Module):
    def __init__(self, vocab_size, hidden_size, num_layers=1):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.rnn = nn.RNN(
            input_size=vocab_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=False,
            bias=True
        )
        self.dense = nn.Linear(hidden_size, vocab_size)

    def forward(self, X, state=None):
        # X shape: (batch, seq) raw indices
        if X.dim() == 2:
            X = X.transpose(0, 1)                     # (seq, batch)
            X = F.one_hot(X.long(), num_classes=self.vocab_size).float()
        elif X.dim() == 3:
            X = X.transpose(0, 1)                     # (seq, batch, vocab)
        else:
            raise ValueError('Unsupported input dimension')

        output, new_state = self.rnn(X, state)        # output: (seq, batch, hidden)
        output = self.dense(output.reshape(-1, output.size(2)))
        return output, new_state


class TrainingWrapper:
    def __init__(self, vocab_size=29, hidden_size=256, lr=1.0):
        self.model = RNNModel(vocab_size, hidden_size)
        self.model.to(torch.float32)
        self.loss_fn = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        self.state = None
        self._updates = 0

    def parameters(self):
        return list(self.model.parameters())

    def buffers(self):
        return []

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        X = inputs[0]
        if self.state is not None:
            self.state = self.state.detach()
        output, new_state = self.model(X, self.state)
        self.state = new_state
        return [output, new_state]

    def loss(self, outputs, labels):
        y_hat = outputs[0]
        Y = labels[0]
        y = Y.transpose(0, 1).reshape(-1)
        return self.loss_fn(y_hat, y)

    def backward(self, loss):
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)

    def step(self):
        self.optimizer.step()
        self._updates += 1

    def optimizer_state(self):
        return [{'updates': self._updates} for _ in self.parameters()]


def build_training(context):
    vocab_size = 29
    hidden_size = 256
    if hasattr(context, 'parameters') and context.parameters:
        p0 = context.parameters[0]
        if hasattr(p0, 'shape') and len(p0.shape) >= 2:
            hidden_size = p0.shape[0]
            vocab_size = p0.shape[1]
    return TrainingWrapper(vocab_size=vocab_size, hidden_size=hidden_size, lr=1.0)


def predict(prefix, num_preds, model, vocab, device):
    model.eval()
    outputs = [vocab[prefix[0]]]
    state = None
    with torch.no_grad():
        for c in prefix[1:]:
            X = torch.tensor([[outputs[-1]]], dtype=torch.long, device=device)
            if state is None:
                output, state = model(X, None)
            else:
                output, state = model(X, state)
            outputs.append(vocab[c])
        for _ in range(num_preds):
            X = torch.tensor([[outputs[-1]]], dtype=torch.long, device=device)
            output, state = model(X, state)
            next_token = output.argmax(dim=1).item()
            outputs.append(next_token)
    return ''.join(vocab.idx_to_token[i] for i in outputs)


def train_epoch(model, data_loader, optimizer, device):
    model.train()
    state = None
    total_loss = 0.0
    total_tokens = 0
    start_time = time.time()

    for X, Y in data_loader:
        X, Y = X.to(device), Y.to(device)
        if state is not None:
            state = state.detach()
        output, state = model(X, state)
        y = Y.transpose(0, 1).reshape(-1)
        loss = F.cross_entropy(output, y)

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        total_loss += loss.item() * y.numel()
        total_tokens += y.numel()

    ppl = math.exp(total_loss / total_tokens)
    speed = total_tokens / (time.time() - start_time)
    return ppl, speed


if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    batch_size = 32
    num_steps = 35
    max_tokens = 10000
    num_hiddens = 256
    num_epochs = int(os.environ.get('MAX_EPOCH', 500))
    lr = 1.0

    corpus, vocab = load_corpus_time_machine(max_tokens)
    print(f'Vocab size: {len(vocab)}')

    offset = random.randint(0, num_steps - 1)
    num_tokens = ((len(corpus) - offset - 1) // batch_size) * batch_size
    Xs = torch.tensor(corpus[offset:offset + num_tokens], dtype=torch.long)
    Ys = torch.tensor(corpus[offset + 1:offset + 1 + num_tokens], dtype=torch.long)
    Xs = Xs.reshape(batch_size, -1)
    Ys = Ys.reshape(batch_size, -1)
    num_batches = Xs.shape[1] // num_steps

    data_list = []
    label_list = []
    for i in range(0, num_steps * num_batches, num_steps):
        X = Xs[:, i:i + num_steps]
        Y = Ys[:, i:i + num_steps]
        data_list.append(X)
        label_list.append(Y)
    data = torch.cat(data_list, dim=0)
    labels = torch.cat(label_list, dim=0)

    dataset = TensorDataset(data, labels)
    data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    model = RNNModel(vocab_size=len(vocab), hidden_size=num_hiddens)
    model.to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)

    print(predict('time traveller', 10, model, vocab, device))

    last_ppl, last_speed = 0.0, 0.0
    for epoch in range(1, num_epochs + 1):
        ppl, speed = train_epoch(model, data_loader, optimizer, device)
        last_ppl, last_speed = ppl, speed
        if epoch % 10 == 0:
            print(f'epoch {epoch}, perplexity {ppl:.1f}, {speed:.1f} tokens/sec')
            print(predict('time traveller', 50, model, vocab, device))
            print(predict('traveller', 50, model, vocab, device))

    print(f'perplexity: {last_ppl:.1f}, {last_speed:.1f} tokens/sec on {device}')
    print(predict('time traveller', 50, model, vocab, device))
    print(predict('traveller', 50, model, vocab, device))
