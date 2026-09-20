"""Estimate incremental rerun token volume from audited, preserved observations."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
analysis=json.loads((ROOT/'output/experiment-analysis-20260920/analysis.json').read_text())
s=analysis['summaries'];direct=s['main/direct']
rows=[]
for key in ('main/ladim','continuous_role/ladim','without_repair_history/ladim','without_progress_prompt/ladim'):
    v=s[key]
    rows.append({'scope':key,'conditions':v['n'],'previous_accepted':v['accepted'],
        'incremental_tokens_reusing_translation':v['e2e_tokens']-direct['e2e_tokens'],
        'input_tokens':v['e2e_input_tokens']-direct['e2e_input_tokens'],
        'output_tokens':v['e2e_output_tokens']-direct['e2e_output_tokens'],
        'historical_cache_miss_input_tokens':v['e2e_cache_miss_tokens']-direct['e2e_cache_miss_tokens']})
cross=s['cross_language/ladim']
rows.append({'scope':'cross_language/ladim','conditions':18,'previous_accepted':cross['accepted'],
    'incremental_tokens_reusing_translation':cross['healthy_incremental_tokens']+cross['faulty_incremental_tokens'],
    'historic_e2e_tokens':cross['e2e_tokens'],'reused_translation_tokens':693790})
result={'basis':'Observed previous complete runs; estimates are not new model measurements or guarantees.',
    'rows':rows,'main_faulty_subset':{'conditions':9,'incremental_tokens':s['main/ladim']['faulty_incremental_tokens']},
    'main_plus_three_ablation_variants':{'conditions':116,'incremental_tokens':sum(r['incremental_tokens_reusing_translation'] for r in rows[:4])},
    'main_and_cross_language':{'conditions':47,'incremental_tokens':rows[0]['incremental_tokens_reusing_translation']+rows[-1]['incremental_tokens_reusing_translation']},
    'main_three_ablations_and_cross_language':{'conditions':134,'incremental_tokens':sum(r['incremental_tokens_reusing_translation'] for r in rows)},
    'archival_collections_not_recommended':{'controlled_fault50_tokens':39982844,'natural_migration10_tokens':13206863},
    'currency':'n/a: current endpoint tariff and invoice unavailable; input cache mix changes after modifying prompts.',
    'currency_formula':'(cache_hit_input*hit_rate + cache_miss_input*miss_rate + output*output_rate) / 1e6',
    'recommendation':'Retain the frozen small-program method and its completed evidence. First test repository-specific coordination on a new repository. Port generic improvements and run a predeclared small diagnostic comparison before considering a full replacement.'}
out=ROOT/'output/repository-rerun-budget-20260920';out.mkdir(parents=True,exist_ok=True)
(out/'estimates.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
