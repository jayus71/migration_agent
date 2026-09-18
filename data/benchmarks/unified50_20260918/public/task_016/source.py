import torch
import torch.nn.functional as functional

def workload(query, key, value, **options):
    return functional.scaled_dot_product_attention(query, key, value, **options)
