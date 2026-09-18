"""Recheck the two remaining saved edges after installing matplotlib; no inference."""

import json
import os
from pathlib import Path
import replay_intertrans_environment_20260918 as replay


def main():
    replay.IMAGE = 'intertrans-n/python:n18-matplotlib-20260918'
    os.environ['AUTOFIX_CANDIDATE_IMAGE'] = replay.IMAGE
    task = 'd2l_mlp_scratch'
    response = json.loads((replay.ROOT / 'intertrans' / task / 'response.json').read_text())
    edges = [edge for record in response['translation_responses']
             for route in record['paths'] for edge in route['translation_edges']]
    index = json.loads((replay.BASE / 'ascend-torch4ms-n18-348e8cd/artifacts/evidence_index.json').read_text())
    reference = Path(index['tasks'][task]['reference_root'])
    destination = replay.ROOT / 'environment_replay_round2'
    rows = []
    for edge in edges:
        if edge['target_language'] != 'Python':
            continue
        prior = replay.ROOT / 'environment_replay' / task / str(edge['edge_id']) / 'native_response.json'
        measured = json.loads(prior.read_text())['verification_responses'][0]
        errors = '\n'.join(t.get('actual_output', '') for t in measured.get('unit_tests', []))
        assert 'ModuleNotFoundError' in errors and 'matplotlib' in errors
        result = replay.replay(task, edge, reference, replay_root=destination)
        rows.append({'edge_id': edge['edge_id'], 'status': result['status'],
                     'tests': result.get('unit_tests', [])})
    replay.select_and_verify(task, edges, reference, replay_root=destination)
    report = {'real_model_calls': 0, 'image': replay.IMAGE, 'task': task,
              'prior_replays_retained': True, 'rows': rows}
    (destination / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'real_model_calls': 0, 'task': task,
                      'edges': [{'edge_id': r['edge_id'], 'status': r['status']} for r in rows]}))


if __name__ == '__main__':
    main()
