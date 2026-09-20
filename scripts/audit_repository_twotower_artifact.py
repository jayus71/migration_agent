"""Offline arithmetic and test-assertion audit of the archived candidate."""
import ast
from collections import Counter
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]/'output/repository-twotower-20260920'
read=lambda p:json.loads(p.read_text())
summary=read(BASE/'continued/continuation_summary.json')
result=read(BASE/'continued/continuation/result.json')
audit=read(BASE/'continued/continuation/test_assertion_audit.json')
checks={};assertions=0;test_count=0
for name,pair in audit.items():
    checks[name+':test_names']=set(pair['source'])==set(pair['target'])
    for key,source in pair['source'].items():
        target=pair['target'][key];test_count+=1;assertions+=len(source['assertions'])
        checks[name+':'+key+':assertion_count']=len(source['assertions'])==len(target['assertions'])
        checks[name+':'+key+':numeric_literals']=Counter(source['numeric_constants'])==Counter(target['numeric_constants'])
fixtures=read(BASE/'source_fixtures.json')['source_test_initializations']
tree=ast.parse((BASE/'continued/target/tests/test_user_history_enc.py').read_text())
function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_set_source_attention_parameters')
arrays={}
for node in function.body:
    if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='array':
        arrays[node.targets[0].id]=ast.literal_eval(node.value.args[0])
names={'in_proj_weight':'in_proj_weight','in_proj_bias':'in_proj_bias',
       'out_proj_weight':'out_proj.weight','out_proj_bias':'out_proj.bias'}
for i,fixture in enumerate(fixtures):
    for target,source in names.items():
        checks[f'fixture{i}:{target}']=arrays[target]==fixture['source_initial_state']['multihead_attn_layers.0.'+source]
numeric=result['final']['public']['numeric'];per_case={}
for case in ('base','history','position','user','debias','reward','ranker','distillation'):
    subset={k:v for k,v in numeric['checks'].items() if k.startswith(case+'_')}
    measures={k:v for k,v in numeric['measurements'].items() if k.startswith(case+'_')}
    per_case[case]={'checks':len(subset),'failed_checks':[k for k,v in subset.items() if not v],
                    'max_update_relative_l2':max((v for k,v in measures.items() if k.endswith('_update_relative_l2')),default=None),
                    'max_item_embedding_abs_error':max((v for k,v in measures.items() if k.endswith('_item_embedding')),default=None),
                    'max_user_embedding_abs_error':max((v for k,v in measures.items() if k.endswith('_user_embedding')),default=None)}
report={'offline_checks':checks,'offline_checks_passed':all(checks.values()),
        'original_tests':test_count,'original_assertions':assertions,
        'manual_assertion_review':'Reviewed all source and target assertions: shape, bounds, scalar type and exact-value comparisons remain equivalent; np.allclose retains atol=1e-3 and default rtol=1e-5. Test input dimensions and expected numeric values remain unchanged. Source-derived initial weights verified above.',
        'numeric_check_count':len(numeric['checks']),'numeric_failed_checks':sum(not v for v in numeric['checks'].values()),
        'cases':per_case,'continuation_cache_hit_fraction':summary['new_usage']['prompt_cache_hit_tokens']/summary['new_usage']['prompt_tokens'],
        'cumulative_cache_hit_fraction':summary['usage']['prompt_cache_hit_tokens']/summary['usage']['prompt_tokens'],
        'cumulative_output_reasoning_fraction':summary['usage']['reasoning_tokens']/summary['usage']['completion_tokens'],
        'changed_file_count':len(summary['changed_files']),
        'scope':'No execution or API rerun; arithmetic, source fixture, assertion and recorded measurement audit only.'}
(BASE/'artifact_review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('offline_checks','manual_assertion_review')},indent=2))
