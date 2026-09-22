"""Array validation for the forthcoming formal runner, with explicit shapes.

Full arrays belong in compressed NPZ artifacts. Only these summaries are exposed
as agent feedback. This module is not used to rescore frozen development runs.
"""
import numpy as np


def compare_arrays(reference, target, *, atol=1e-7, rtol=1e-5):
    a,b=np.asarray(reference),np.asarray(target)
    if a.shape!=b.shape:
        return {'accepted':False,'reason':'shape_mismatch','reference_shape':list(a.shape),'target_shape':list(b.shape)}
    if a.dtype!=b.dtype:
        return {'accepted':False,'reason':'dtype_mismatch','reference_dtype':str(a.dtype),'target_dtype':str(b.dtype)}
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        return {'accepted':False,'reason':'nonfinite','shape':list(a.shape)}
    difference=np.abs(a-b)
    bound=atol+rtol*np.abs(a)
    return {'accepted':bool(np.all(difference<=bound)), 'shape':list(a.shape),
            'max_abs_difference':float(difference.max(initial=0)),
            'relative_l2_difference':float(np.linalg.norm((a-b).ravel())/max(np.linalg.norm(a.ravel()),atol)),
            'mismatched_elements':int(np.count_nonzero(difference>bound)),
            'elements':int(a.size),'atol':atol,'rtol':rtol}


def compare_named_arrays(reference,target,**kwargs):
    if reference.keys()!=target.keys():
        return {'accepted':False,'reason':'parameter_keys_mismatch',
                'missing':sorted(reference.keys()-target.keys()),'extra':sorted(target.keys()-reference.keys())}
    checks={k:compare_arrays(reference[k],target[k],**kwargs) for k in sorted(reference)}
    return {'accepted':all(x['accepted'] for x in checks.values()),'parameters':checks}
