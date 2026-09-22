"""Download a predetermined public-source pool before observing repair outcomes.

This prepares provenance only; it does not claim to freeze a runnable formal
benchmark or generate target programs. All sources retain original bytes.
"""
from pathlib import Path
import hashlib
import json
import urllib.request

REVISION = 'acc295dc7b90714f1bf47f06004fc19a7fe235c4'
SOURCES = {
    'mnist/main.py': [('cnn_classifier', 'Net', 'convolutional')],
    'super_resolution/model.py': [('super_resolution', 'Net', 'convolutional')],
    'vae/main.py': [('variational_autoencoder', 'VAE', 'generative')],
    'dcgan/main.py': [('gan_generator', 'Generator', 'generative')],
    'word_language_model/model.py': [('recurrent_language_model', 'RNNModel', 'sequence'), ('transformer_language_model', 'TransformerModel', 'sequence')],
    'time_sequence_prediction/train.py': [('time_sequence', 'Sequence', 'sequence')],
    'reinforcement_learning/actor_critic.py': [('actor_critic', 'Policy', 'policy')],
    'reinforcement_learning/reinforce.py': [('reinforce', 'Policy', 'policy')],
}


def main():
    root = Path(__file__).resolve().parent / 'formal_source_pool'
    root.mkdir(exist_ok=False)
    records = []
    for name in [*SOURCES, 'LICENSE']:
        url = f'https://raw.githubusercontent.com/pytorch/examples/{REVISION}/{name}'
        content = urllib.request.urlopen(url, timeout=60).read()
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        records.append({'path':name,'url':url,'sha256':hashlib.sha256(content).hexdigest(),
                        'tasks':SOURCES.get(name,[])})
    (root/'manifest.json').write_text(json.dumps({'status':'source pool frozen; runnable contracts pending',
        'repository':'https://github.com/pytorch/examples','revision':REVISION,
        'selection':'Eight public source files, nine named program tasks in four families, selected before development API results. No outcome filtering.',
        'target':'Native JAX/Optax candidates must be generated from these sources and the public contract; no injected faults or hidden healthy target.',
        'sources':records},indent=2)+'\n')


if __name__=='__main__': main()
