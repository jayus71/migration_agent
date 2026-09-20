"""Short source-side feasibility checks only: no migration, LLM or source edits."""
import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import runpy
import types
from datetime import date, timedelta


def worker(base, name):
    import numpy as np
    import torch
    torch.set_num_threads(1)
    torch.manual_seed(101)
    np.random.seed(101)
    if name == 'time_series_core':
        path = base / 'time-series-forecasting-pytorch/project.py'
        tree = ast.parse(path.read_text())
        definitions = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and not getattr(n, 'name', '') == 'download_data']
        namespace = dict(np=np, torch=torch, nn=torch.nn, Dataset=torch.utils.data.Dataset)
        exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), 'exec'), namespace)
        values = np.sin(np.arange(180) / 11) + np.arange(180) * 0.01 + 10
        scaler = namespace['Normalizer']()
        values = scaler.fit_transform(values)
        x, unseen = namespace['prepare_data_x'](values, 20)
        y = namespace['prepare_data_y'](values, 20)
        dataset = namespace['TimeSeriesDataset'](x, y)
        loader = torch.utils.data.DataLoader(dataset, batch_size=16, shuffle=False)
        model = namespace['LSTMModel']()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01, betas=(0.9, 0.98), eps=1e-9)
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=40, gamma=0.1)
        namespace.update(model=model, optimizer=optimizer, scheduler=scheduler,
                         criterion=torch.nn.MSELoss(), config={'training': {'device': 'cpu'}})
        before = {k: v.clone() for k, v in model.state_dict().items()}
        train_loss, _ = namespace['run_epoch'](loader, is_training=True)
        eval_loss, _ = namespace['run_epoch'](loader)
        forecast = model(torch.tensor(unseen.copy()).float()[None, :, None])
        assert np.isfinite(train_loss) and np.isfinite(eval_loss) and torch.isfinite(forecast).all()
        assert any(not torch.equal(before[k], v) for k, v in model.state_dict().items())
        assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
        return {'status': 'passed', 'scope': 'Original preprocessing, dataset, LSTM, run_epoch train/eval and forecast; synthetic data, 1 CPU epoch. Online API and plots not executed.',
                'parameter_count': sum(p.numel() for p in model.parameters()),
                'train_loss': train_loss, 'eval_loss': eval_loss, 'forecast_shape': list(forecast.shape)}
    if name == 'simple_moe_core':
        sys.path.insert(0, str(base / 'simple-moe'))
        from src.models.moe import MixtureOfExperts
        from src.models import _model_stack
        model = MixtureOfExperts(input_dim=8, output_dim=3, num_experts=4, k=2,
                                 expert_kwargs={'hidden_dim': 16})
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        x, y = torch.randn(16, 8), torch.randint(0, 3, (16,))
        losses = []
        before = {k: v.clone() for k, v in model.state_dict().items()}
        for _ in range(3):
            model.train()
            optimizer.zero_grad()
            prediction, aux = model(x)
            loss = torch.nn.functional.cross_entropy(prediction, y) + 0.1 * aux
            loss.backward()
            optimizer.step()
            assert torch.isfinite(loss) and all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
            losses.append(float(loss.detach()))
        model.eval()
        prediction, aux = model(x)
        assert aux is None and torch.isfinite(prediction).all()
        assert any(not torch.equal(before[k], v) for k, v in model.state_dict().items())
        return {'status': 'passed', 'scope': 'Original model/router/experts, 3 Adam steps, default router noise and expert dropout, CPU.',
                'parameter_count': sum(p.numel() for p in model.parameters()), 'losses': losses,
                'external_linear_active': _model_stack._runtime_linear_module is not None,
                'external_router_active': _model_stack._runtime_topk_router is not None}
    if name == 'simple_moe_trainer':
        sys.path.insert(0, str(base / 'simple-moe'))
        from src.models.moe import MixtureOfExperts
        from src.training.trainer import MoETrainer
        from src.evaluation.metrics import MoEMetrics
        model = MixtureOfExperts(input_dim=8, output_dim=3, num_experts=4, k=2,
                                 expert_kwargs={'hidden_dim': 16})
        data = torch.utils.data.TensorDataset(torch.randn(32, 8), torch.randint(0, 3, (32,)))
        loader = torch.utils.data.DataLoader(data, batch_size=8)
        trainer = MoETrainer(model, torch.nn.CrossEntropyLoss(), torch.optim.Adam(model.parameters()), torch.device('cpu'))
        train_metrics = trainer.train_epoch(loader, 0)
        eval_metrics = trainer.evaluate(loader)
        return {'status': 'passed', 'scope': 'Original full trainer train/evaluate entry, 1 synthetic CPU epoch; metrics module imported.',
                'train_metrics': {k: float(v.detach()) if torch.is_tensor(v) else v for k, v in train_metrics.items()},
                'eval_metrics': {k: float(v.detach()) if torch.is_tensor(v) else v for k, v in eval_metrics.items()}}
    if name == 'simple_moe_metrics':
        sys.path.insert(0, str(base / 'simple-moe'))
        from src.evaluation.metrics import MoEMetrics
        metrics = MoEMetrics(num_experts=4)
        values = metrics.compute_metrics(torch.softmax(torch.randn(8, 4), dim=-1))
        return {'status': 'passed', 'metrics': values}
    if name == 'time_series_entry':
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import alpha_vantage.timeseries
        # Replace external data acquisition with an explicit test fixture;
        # retain the original download_data parser and complete script body.
        class FixtureTimeSeries:
            def __init__(self, *args, **kwargs):
                pass
            def get_daily_adjusted(self, *args, **kwargs):
                data = {(date(2020, 1, 1) + timedelta(days=i)).isoformat():
                        {'5. adjusted close': str(100 + 0.1 * i + np.sin(i / 11))}
                        for i in reversed(range(180))}
                return data, {'fixture': '180 deterministic synthetic daily prices'}
        alpha_vantage.timeseries.TimeSeries = FixtureTimeSeries
        grid = plt.grid
        def legacy_grid(*args, **kwargs):
            if 'b' in kwargs:
                kwargs['visible'] = kwargs.pop('b')
            return grid(*args, **kwargs)
        plt.grid = legacy_grid
        namespace = runpy.run_path(str(base / 'time-series-forecasting-pytorch/project.py'), run_name='__main__')
        assert np.isfinite(namespace['prediction']).all()
        model = namespace['model']
        result = {'status': 'passed', 'scope': 'Unmodified complete project.py; all 100 default epochs, validation and forecast, 180-row synthetic API fixture, CPU.',
                  'environment_adaptations': ['Alpha Vantage response replaced by fixed local fixture; no external API request.',
                                              'Matplotlib legacy grid(b=...) translated to grid(visible=...); headless Agg backend.'],
                  'epochs': namespace['config']['training']['num_epoch'],
                  'parameter_count': sum(p.numel() for p in model.parameters()),
                  'plot_count': len(plt.get_fignums()),
                  'forecast_shape': list(namespace['prediction'].shape)}
        plt.close('all')
        return result
    raise ValueError(name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--worker')
    args = parser.parse_args()
    if args.worker:
        try:
            result = worker(args.base.resolve(), args.worker)
        except Exception as exc:
            result = {'status': 'failed', 'error': f'{type(exc).__name__}: {exc}', 'traceback': traceback.format_exc()}
        args.out.write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
        return
    args.out.mkdir(parents=True, exist_ok=True)
    environment = {k: v for k, v in os.environ.items() if not any(w in k.upper() for w in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL'))}
    environment.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='', JAX_PLATFORMS='cpu', MPLBACKEND='Agg', PYTHONDONTWRITEBYTECODE='1')
    tasks = [
        ('two_tower_tests', 'two_tower_models', ['-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests']),
        ('two_tower_training', 'two_tower_models', ['-m', 'train.train', '--num_epochs', '1', '--num_samples', '32', '--batch_size', '8']),
        ('simple_moe_tests', 'simple-moe', ['-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests']),
    ]
    for name in ('time_series_core', 'simple_moe_core', 'simple_moe_trainer'):
        tasks.append((name, '.', [str(Path(__file__).resolve()), '--base', str(args.base.resolve()), '--out', str((args.out / (name + '.json')).resolve()), '--worker', name]))
    rows = []
    for name, directory, command in tasks:
        started = time.monotonic()
        process = subprocess.run([sys.executable, *command], cwd=args.base / directory,
                                 env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        (args.out / (name + '.log')).write_text(process.stdout)
        rows.append({'check': name, 'returncode': process.returncode, 'seconds': time.monotonic() - started,
                     'tail': process.stdout[-3500:]})
    modules = {}
    for module in ('torch', 'jax', 'flax', 'optax', 'pytest', 'numpy', 'matplotlib', 'alpha_vantage', 'tensorboard', 'sklearn'):
        try:
            modules[module] = importlib.util.find_spec(module) is not None
        except ModuleNotFoundError:
            modules[module] = False
    summary = {'python': sys.executable, 'module_available': modules, 'checks': rows, 'real_model_calls': 0}
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
