"""One acceptance rule over predeclared measurements for every method."""

import numpy as np


def compare(reference, target, *, backend_required=True):
    if reference.get('status') != 'completed':
        return {'accepted': None, 'status': 'reference_unavailable', 'checks': {}}
    if target.get('status') != 'completed':
        return {'accepted': False, 'status': 'candidate_execution_failed', 'checks': {},
                'unavailable': list(reference['values'])}
    if not isinstance(target.get('values'), dict) or not isinstance(target.get('schema'), dict):
        return {'accepted': False, 'status': 'malformed_measurement', 'checks': {'well_formed': False},
                'unavailable': list(reference['values'])}
    checks = {'schema_equal': reference['schema'] == target.get('schema'),
              'seed_equal': reference.get('seed') == target.get('seed'),
              'measurement_names_equal': set(reference['values']) == set(target.get('values') or {}),
              'backend_observed': not backend_required or target.get('backend', {}).get('observed') is True}
    differences = {}
    for name, expected in reference['values'].items():
        actual = target['values'].get(name)
        if expected is None:
            checks[name] = actual is None and name in target['values']
            differences[name] = None
            continue
        if actual is None:
            checks[name] = False
            differences[name] = None
            continue
        try:
            a, b = np.asarray(expected), np.asarray(actual)
            finite = bool(np.isfinite(a).all() and np.isfinite(b).all())
        except (TypeError, ValueError):
            checks[name] = False
            differences[name] = None
            continue
        atol, rtol = (1e-5, 1e-3) if name.startswith('update/') else (1e-4, 1e-3) if name.startswith('gradient/') else (1e-4, 1e-4)
        if 'matmul_bfloat16' in name:
            atol = .01
        if name.startswith(('initial/', 'trainable/')):
            atol, rtol = 0, 0
        valid = a.shape == b.shape and finite
        checks[name] = bool(valid and np.allclose(a, b, atol=atol, rtol=rtol))
        differences[name] = float(np.max(np.abs(a.astype(float) - b.astype(float)))) if valid and a.size else None
    return {'accepted': bool(checks) and all(checks.values()), 'status': 'evaluated',
            'checks': checks, 'differences': differences}
