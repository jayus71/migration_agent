import argparse
import os
import re
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# ---------------------------------------------------------------------------
# Text preprocessing helpers (translated from DJL)
# ---------------------------------------------------------------------------

class SimpleTokenizer:
    def __call__(self, text):
        return text.split()

class LowerCaseConvertor:
    def __init__(self, locale=None):
        self.locale = locale
    def __call__(self, tokens):
        return [t.lower() for t in tokens]

class PunctuationSeparator:
    def __call__(self, tokens):
        out = []
        for t in tokens:
            out.extend(re.findall(r"[a-zA-Z0-9]+|[^\sa-zA-Z0-9]", t))
        return out

class TextTruncator:
    def __init__(self, max_length):
        self.max_length = max_length
    def __call__(self, tokens):
        return tokens[:self.max_length]

class TextTerminator:
    def __call__(self, tokens):
        return tokens + ["<eos>"]

# ---------------------------------------------------------------------------
# Dataset (simplified Tatoeba English-French)
# ---------------------------------------------------------------------------

class TatoebaEnglishFrenchDataset(Dataset):
    def __init__(self, path, source_processors, target_processors,
                 source_vocab=None, target_vocab=None, limit=None):
        self.path = path
        self.source_processors = source_processors
        self.target_processors = target_processors
        self.source_vocab = source_vocab or {}
        self.target_vocab = target_vocab or {}
        self.source_data = []
        self.target_data = []
        self._load(limit)

    def _apply(self, tokens, processors):
        for p in processors:
            tokens = p(tokens)
        return tokens

    def _load(self, limit):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Dataset file not found: {self.path}")
        with open(self.path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                parts = line.strip().split('\t')
                if len(parts) < 2:
                    continue
                src_text, tgt_text = parts[0], parts[1]
                src_tokens = self._apply(src_text.split(), self.source_processors)
                tgt_tokens = self._apply(tgt_text.split(), self.target_processors)
                self.source_data.append(src_tokens)
                self.target_data.append(tgt_tokens)

        # Build vocabularies if not provided
        if not self.source_vocab:
            self.source_vocab = {"<pad>": 0, "<unk>": 1}
            for tokens in self.source_data:
                for t in tokens:
                    if t not in self.source_vocab:
                        self.source_vocab[t] = len(self.source_vocab)
        if not self.target_vocab:
            self.target_vocab = {"<pad>": 0, "<unk>": 1, "<eos>": 2}
            for tokens in self.target_data:
                for t in tokens:
                    if t not in self.target_vocab:
                        self.target_vocab[t] = len(self.target_vocab)

    def __len__(self):
        return len(self.source_data)

    def __getitem__(self, idx):
        src = [self.source_vocab.get(t, 1) for t in self.source_data[idx]]
        tgt = [self.target_vocab.get(t, 1) for t in self.target_data[idx]]
        return torch.tensor(src, dtype=torch.long), torch.tensor(tgt, dtype=torch.long)

    def collate_fn(self, batch):
        src_batch, tgt_batch = zip(*batch)
        src_lengths = torch.tensor([len(s) for s in src_batch], dtype=torch.long)
        tgt_lengths = torch.tensor([len(t) for t in tgt_batch], dtype=torch.long)
        src_padded = nn.utils.rnn.pad_sequence(src_batch, batch_first=True, padding_value=0)
        tgt_padded = nn.utils.rnn.pad_sequence(tgt_batch, batch_first=True, padding_value=0)
        return (src_padded, src_lengths), (tgt_padded, tgt_lengths)

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class Seq2SeqModel(nn.Module):
    def __init__(self, source_vocab_size, target_vocab_size):
        super().__init__()
        self.encoder_embedding = nn.Embedding(source_vocab_size, 32)
        self.encoder_lstm = nn.LSTM(32, 32, num_layers=2, batch_first=True, dropout=0)
        self.decoder_embedding = nn.Embedding(target_vocab_size, 32)
        self.decoder_lstm = nn.LSTM(32, 32, num_layers=2, batch_first=True, dropout=0)
        self.decoder_linear = nn.Linear(32, target_vocab_size)

    def forward(self, source_tokens, source_lengths, target_tokens, target_lengths):
        # Encoder
        src_emb = self.encoder_embedding(source_tokens)  # [B, S, 32]
        sorted_lengths, sorted_idx = torch.sort(source_lengths, descending=True)
        sorted_src_emb = src_emb[sorted_idx]
        packed_src = nn.utils.rnn.pack_padded_sequence(
            sorted_src_emb, sorted_lengths.cpu(), batch_first=True
        )
        _, (h_n, c_n) = self.encoder_lstm(packed_src)
        # Unsort
        unsorted_idx = torch.argsort(sorted_idx)
        h_n = h_n[:, unsorted_idx, :]
        c_n = c_n[:, unsorted_idx, :]

        # Decoder
        tgt_emb = self.decoder_embedding(target_tokens)  # [B, T, 32]
        decoder_output, _ = self.decoder_lstm(tgt_emb, (h_n, c_n))
        logits = self.decoder_linear(decoder_output)  # [B, T, V]
        return logits

# ---------------------------------------------------------------------------
# Loss
# ---------------------------------------------------------------------------

class MaskedSoftmaxCrossEntropyLoss(nn.Module):
    def forward(self, logits, target_tokens, target_lengths):
        # logits: [B, T, V], target_tokens: [B, T], target_lengths: [B]
        batch, seq, vocab = logits.shape
        loss_per_token = F.cross_entropy(
            logits.transpose(1, 2), target_tokens, reduction='none'
        )  # [B, T]
        mask = torch.arange(seq, device=logits.device).unsqueeze(0) < target_lengths.unsqueeze(1)
        loss_per_token = loss_per_token * mask.float()
        loss_per_sample = loss_per_token.sum(dim=1) / target_lengths.float()
        return loss_per_sample.unsqueeze(1)  # [B, 1]

# ---------------------------------------------------------------------------
# Trainer implementing the common interface
# ---------------------------------------------------------------------------

class Seq2SeqTrainer:
    def __init__(self, context=None):
        # Metadata fixed vocabulary sizes
        self.source_vocab_size = 6
        self.target_vocab_size = 5
        self.model = Seq2SeqModel(self.source_vocab_size, self.target_vocab_size)
        self.optimizer = optim.Adam(
            self.model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8
        )
        self._parameters = list(self.model.parameters())
        self._buffers = list(self.model.buffers())
        self.loss_fn = MaskedSoftmaxCrossEntropyLoss()

    def parameters(self):
        return self._parameters

    def buffers(self):
        return self._buffers

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        source_tokens, source_lengths = inputs
        target_tokens, target_lengths = labels
        logits = self.model(source_tokens, source_lengths, target_tokens, target_lengths)
        return [logits]

    def loss(self, outputs, labels):
        logits = outputs[0]
        target_tokens, target_lengths = labels
        return self.loss_fn(logits, target_tokens, target_lengths)

    def backward(self, loss):
        loss.sum().backward()

    def step(self):
        self.optimizer.step()

    def optimizer_state(self):
        states = []
        for p in self._parameters:
            state = self.optimizer.state[p]
            if len(state) == 0:
                states.append({"updates": 0})
            else:
                step_val = state["step"]
                if isinstance(step_val, torch.Tensor):
                    step_val = step_val.item()
                states.append({
                    "updates": int(step_val),
                    "means": state["exp_avg"],
                    "variances": state["exp_avg_sq"]
                })
        return states

def build_training(context=None):
    return Seq2SeqTrainer(context)

# ---------------------------------------------------------------------------
# Main entry point (training loop)
# ---------------------------------------------------------------------------

def run_example(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--epoch', type=int, default=10)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--output-dir', type=str, default='build')
    parser.add_argument('--max-gpus', type=int, default=0)
    parser.add_argument('--data-path', type=str, default='fra-eng.txt')
    parsed = parser.parse_args(args)

    # Preprocessing pipelines matching the Java source
    source_processors = [
        SimpleTokenizer(),
        LowerCaseConvertor(),
        PunctuationSeparator(),
        TextTruncator(10),
    ]
    target_processors = [
        SimpleTokenizer(),
        LowerCaseConvertor(),
        PunctuationSeparator(),
        TextTruncator(8),
        TextTerminator(),
    ]

    dataset = TatoebaEnglishFrenchDataset(
        path=parsed.data_path,
        source_processors=source_processors,
        target_processors=target_processors,
        limit=parsed.limit if parsed.limit > 0 else None
    )

    # Build model and trainer
    trainer = build_training(None)

    # Override vocab sizes based on actual dataset (for main training only)
    src_vocab_size = len(dataset.source_vocab)
    tgt_vocab_size = len(dataset.target_vocab)
    trainer.model = Seq2SeqModel(src_vocab_size, tgt_vocab_size)
    trainer.optimizer = optim.Adam(
        trainer.model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8
    )
    trainer._parameters = list(trainer.model.parameters())
    trainer.loss_fn = MaskedSoftmaxCrossEntropyLoss()

    device = torch.device("cuda" if parsed.max_gpus > 0 and torch.cuda.is_available() else "cpu")
    trainer.model.to(device)

    dataloader = DataLoader(
        dataset,
        batch_size=parsed.batch_size,
        shuffle=True,
        collate_fn=dataset.collate_fn
    )

    for epoch in range(parsed.epoch):
        trainer.model.train()
        total_loss = 0.0
        for inputs, labels in dataloader:
            source_tokens, source_lengths = inputs
            target_tokens, target_lengths = labels
            source_tokens = source_tokens.to(device)
            source_lengths = source_lengths.to(device)
            target_tokens = target_tokens.to(device)
            target_lengths = target_lengths.to(device)

            trainer.zero_grad()
            outputs = trainer.forward([source_tokens, source_lengths],
                                      [target_tokens, target_lengths])
            loss = trainer.loss(outputs, [target_tokens, target_lengths])
            trainer.backward(loss)
            trainer.step()
            total_loss += loss.sum().item()

        avg_loss = total_loss / len(dataset)
        print(f"Epoch {epoch+1}/{parsed.epoch}, Loss: {avg_loss:.4f}")

        # Save checkpoint
        os.makedirs(parsed.output_dir, exist_ok=True)
        torch.save(trainer.model.state_dict(),
                   os.path.join(parsed.output_dir, f"seq2seq_epoch_{epoch+1}.pt"))

if __name__ == '__main__':
    run_example()
