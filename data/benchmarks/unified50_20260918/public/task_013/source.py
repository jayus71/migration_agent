import torch
import torch.nn.functional as functional

def attention_workload(query, key, value, **options):
    return functional.scaled_dot_product_attention(query, key, value, **options)

def embedding_workload(indices, weight):
    return functional.embedding(indices, weight)
