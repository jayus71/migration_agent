"""Validate and archive the 60 existing E conditions; no execution or API calls."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import tarfile

TASKS = ['image_mlp', 'cnn', 'resnet', 'transformer_classifier', 'tiny_causal_lm']
METHODS = {'T-MSA': 'MSAdapter 0.6.0 CPU', 'T-CTE': 'CodeTransEngine translation-only',
           'Direct': 'Direct', 'Frozen Translator': 'Frozen Translator'}
EXPECTED = {'T-MSA': (0,15,0,0), 'T-CTE': (8,12,12,33702),
            'Direct': (7,13,13,361566), 'Frozen Translator': (15,15,15,287550)}

def read(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def csvsave(p, rows):
    with p.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v,(dict,list)) else v
                    for k,v in r.items()} for r in rows)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1] / 'output/e-baselines-current-20260918')
    args = parser.parse_args()
    root = args.root.resolve()
    out = root / 'four_methods'
    out.mkdir(exist_ok=True)
    new = root / 'e-existing-translations-20260918'
    assert sha(root/'e-existing-translations-20260918-archive.tar.gz') == 'a7378c0f735a2e3bced94603c10c353de94f5b577512aafd0bce6c875c6d362c'
    old = root/'formal'
    manifests = [read(old/'manifest.json'), read(new/'manifest.json')]
    verifier_hash = sha(old/'frozen_code/verify_t_direct_candidate.py')
    assert verifier_hash == sha(new/'verify_t_direct_candidate.py')
    assert all(m['verifier_sha256'] == verifier_hash for m in manifests)
    assert all(m.get('new_api_calls',m.get('new_model_calls')) == 0 for m in manifests)
    preflight = read(old/'preflight.json')
    assert preflight['passed'] and preflight['verifier_sha256'] == verifier_hash
    audit = read(root/'translator_reuse_audit.json')
    assert audit == read(new/'Frozen_Translator_provenance.json')
    assert all(r['candidate_is_exact_patch_v0'] and r['fixer_calls']==0 and r['final_iter']==0 for r in audit['rows'])
    provenance = {'T-MSA': read(old/'provenance/T-MSA_source_summary.json')['rows'],
                  'T-CTE': read(old/'provenance/T-CTE_source_summary.json')['rows'],
                  'Direct': read(new/'Direct_provenance.json')['rows'], 'Frozen Translator': audit['rows']}
    records = []
    for folder, manifest in zip([old,new],manifests):
        summary = read(folder/'summary.json')
        assert summary['complete'] and len(summary['rows']) == 30
        assert len(manifest['jobs']) == 30
        jobs = {(r['method'],r['task'],r['seed']):r for r in manifest['jobs']}
        for r in summary['rows']:
            method, task, seed = r['method'],r['task'],r['seed']
            job = jobs[(method,task,seed)]
            assert all(r[k] == v for k,v in job.items())
            case = old/'runs'/method/f'{task}_{seed}' if folder==old else new/method.replace(' ','_')/f'{task}_{seed}'
            assert sha(case/'source.py') == r['source_sha256']
            assert sha(case/'candidate.py') == r['candidate_sha256']
            v = read(case/'verification.json')
            assert v == r['verification'] and v['seed'] == seed and v['task'] == task
            for f in ['stdout.txt','stderr.txt']:
                assert (case/f).is_file()
            origin = [x for x in provenance[method] if x.get('task',x.get('task_id'))==task and x['seed']==seed]
            assert len(origin)==1
            origin = origin[0]
            assert origin.get('source_sha256',origin.get('source_hash')) == r['source_sha256']
            previous = r.get('original_accepted',r.get('original_strict'))
            assert previous == origin.get('historical_strict_accepted',origin.get('strict_success'))
            if method=='Frozen Translator':
                assert origin['candidate_sha256'] == r['candidate_sha256']
            tokens = r.get('historical_tokens',r.get('original_total_tokens'))
            if method=='T-MSA':
                tokens=0
            else:
                assert tokens == origin.get('historical_translator_tokens',origin.get('total_tokens'))
            c = v.get('comparison',{})
            for k,expected in [('loss_abs_threshold',.02),('grad_norm_abs_threshold',.05),('param_update_rel_l2_threshold',.03)]:
                assert c.get(k)==expected
            metrics = {k:c.get(k) for k in ['last_step_abs_loss_diff','last_step_abs_grad_norm_diff','param_update_rel_l2']}
            if not v['training_success']:
                assert all(x is None for x in metrics.values())
            if v['translation_success_at_1']:
                assert v['execution_success'] and v['training_success']
                assert metrics['last_step_abs_loss_diff']<=.02 and metrics['last_step_abs_grad_norm_diff']<=.05 and metrics['param_update_rel_l2']<=.03
                assert c['buffer_state']['matched']
            if method!='T-MSA':
                assert previous == v['translation_success_at_1']
            records.append(dict(method=METHODS[method],method_id=method,task=task,seed=seed,
                repeat=seed-641,strict_accepted=v['translation_success_at_1'],forward_completed=v['execution_success'],
                training_completed=v['training_success'],historical_accepted=previous,
                historical_tokens=tokens,usage_kind='no_llm' if method=='T-MSA' else 'estimated' if method=='T-CTE' else 'historical_reported_usage',
                new_api_calls=0,new_api_tokens=0,source_sha256=r['source_sha256'],candidate_sha256=r['candidate_sha256'],
                verification_sha256=sha(case/'verification.json'),case_path=case.relative_to(root).as_posix(),
                candidate_origin=r.get('candidate_origin',r.get('original_candidate')),backend=v['backend_path'],
                runtime=v.get('runtime'),initial_state_exact=v.get('initial_state_agreement',{}).get('exact'),
                **metrics,buffer_matched=c.get('buffer_state',{}).get('matched'),errors=v['errors']))
    assert len(records)==60 and len({(r['method_id'],r['task'],r['seed']) for r in records})==60
    summaries=[]
    per_task=[]
    for method in METHODS:
        rows=[r for r in records if r['method_id']==method]
        assert {(r['task'],r['seed']) for r in rows} == {(t,s) for t in TASKS for s in [642,643,644]}
        values=tuple(sum(r[k] for r in rows) for k in ['strict_accepted','forward_completed','training_completed','historical_tokens'])
        assert values==EXPECTED[method]
        count=len({r['candidate_sha256'] for r in rows})
        summaries.append(dict(method=METHODS[method],conditions=15,candidate_artifacts=5 if method=='T-MSA' else 15,
            distinct_candidate_hashes=count,strict_accepted=values[0],forward_completed=values[1],training_completed=values[2],
            historical_tokens=values[3],usage_kind=rows[0]['usage_kind'],new_api_calls=0,new_api_tokens=0,seeds=[642,643,644],
            execution_or_initialization_failures=sum(not r['forward_completed'] for r in rows),
            training_failures_after_forward=sum(r['forward_completed'] and not r['training_completed'] for r in rows),
            strict_failures_after_training=sum(r['training_completed'] and not r['strict_accepted'] for r in rows)))
        for task in TASKS:
            selected=[r for r in rows if r['task']==task]
            per_task.append(dict(method=METHODS[method],task=task,conditions=3,
                distinct_candidate_hashes=len({r['candidate_sha256'] for r in selected}),
                strict_accepted=sum(r['strict_accepted'] for r in selected),
                forward_completed=sum(r['forward_completed'] for r in selected),training_completed=sum(r['training_completed'] for r in selected)))
    for task in TASKS:
        assert len({r['source_sha256'] for r in records if r['task']==task})==1
    save(out/'summary.json',dict(complete=True,conditions=60,verifier_sha256=verifier_hash,summaries=summaries,per_task=per_task,rows=records))
    csvsave(out/'summary.csv',summaries)
    csvsave(out/'conditions.csv',records)
    csvsave(out/'per_task.csv',per_task)
    save(out/'validation.json',dict(passed=True,conditions_checked=60,source_and_candidate_hash_checks=120,
        verification_json_matches=60,original_outcomes_preserved_llm_conditions=45,
        same_verifier_for_all=True,verifier_sha256=verifier_hash,new_model_calls=0,
        missing_numeric_measurements_preserved=True,complete_task_seed_grid=True,
        new_download_remote_sha256=sha(root/'e-existing-translations-20260918-archive.tar.gz')))
    (out/'summarize_e_four_methods_20260918.py').write_bytes(Path(__file__).read_bytes())
    files = sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                   and p.name not in ['e-four-methods-60-20260918.tar.gz','archive_receipt.json','file_manifest.json'])
    entries=[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    save(out/'file_manifest.json',dict(files=entries,file_count=len(entries)))
    archive=out/'e-four-methods-60-20260918.tar.gz'
    with tarfile.open(archive,'w:gz') as tf:
        for p in files+[out/'file_manifest.json']:
            tf.add(p,arcname='e-baselines-current-20260918/'+p.relative_to(root).as_posix(),recursive=False)
    with tarfile.open(archive) as tf:
        for e in entries:
            f=tf.extractfile('e-baselines-current-20260918/'+e['path'])
            assert hashlib.sha256(f.read()).hexdigest()==e['sha256']
    save(out/'archive_receipt.json',dict(archive=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,
        archived_file_count=len(entries)+1,all_member_hashes_verified=True,file_manifest_sha256=sha(out/'file_manifest.json')))
    print(json.dumps(dict(summaries=summaries,per_task=per_task,archive=read(out/'archive_receipt.json')),ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
