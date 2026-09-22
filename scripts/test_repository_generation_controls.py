"""Offline checks for bounded generation and shared evaluation integration."""
import json
from pathlib import Path
import tempfile
from dataclasses import replace
import repository_migration_experiment as c
from repository_shared_translation import units_for, translate


def main():
    checks = {}
    with tempfile.TemporaryDirectory(prefix='generation-preflight-') as tmp:
        logs = Path(tmp)
        for repo in c.REPOSITORIES:
            root = c.bind(repo)
            ws = root / 'preflight/workspace'
            ev = c.evaluator(repo, ws, logs / repo / 'evidence')
            tools = c.WorkspaceTools(ws, lambda x: {}, named_tests=('public',), validate_syntax=True)
            def no_api(*args):
                raise AssertionError('No API')
            agent = c.AutonomousAgent(tools, logs / repo / 'generator',
                config=replace(c.configuration('swe'), max_calls=48, max_output_tokens=240000), client=no_api)
            checks[repo + ':generator_constructed_without_model'] = agent.calls == 0
            checks[repo + ':coverage_reports_acceptance'] = 'accepted' in ev.tool({'test': 'coverage'})
        root = c.bind('twotower')
        units = units_for(root / 'source')
        planned = {n for u in units for n in u['files']}
        checks['all_nonempty_python_in_plan'] = all(p.relative_to(root / 'source').as_posix() in planned
            for p in (root / 'source').rglob('*.py') if p.read_text().strip())
        checks['metadata_last'] = units[-1]['files'] == ['parameter_map.json', 'requirements.txt', 'README.md']
        ws = logs / 'fixture/workspace'
        for name in ('source', 'target', 'scratch_tests'):
            (ws / name).mkdir(parents=True)
        (ws / 'source/a.py').write_text('answer = 1\n')
        (ws / 'source/README.md').write_text('Example')
        (ws / 'task.json').write_text('{}')
        counter = [0]
        def fake(request, timeout):
            counter[0] += 1
            if counter[0] == 1:
                content, finish = '', 'length'
            else:
                payload = json.loads(request['messages'][1]['content'])
                files = {n: ('{}' if n.endswith('.json') else 'answer = 1\n' if n.endswith('.py') else 'mindspore')
                    for n in payload['files_to_generate']}
                content, finish = json.dumps({'files': files}), 'stop'
            return {'model': 'offline', 'choices': [{'finish_reason': finish, 'message': {'role': 'assistant',
                'content': content, 'reasoning_content': 'offline'}}],
                'usage': {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5}}
        agent = c.AutonomousAgent(c.WorkspaceTools(ws, lambda x: {}, named_tests=('public',)), logs / 'fixture/agent',
            config=replace(c.configuration('swe'), max_calls=48, max_output_tokens=240000), client=fake)
        result = translate(agent, ws, {}, c.save, logs / 'fixture/translation')
        checks['generation_retry_keeps_cost'] = agent.calls == 3 and agent.usage()['total_tokens'] == 15
        checks['generation_plan_completes'] = result['unattempted_units'] == 0 and all(x['status'] == 'generated' for x in result['units'])
        checks['generation_does_not_invoke_tests'] = not agent.tools.edit_records
    record = {'passed': all(checks.values()), 'checks': checks, 'real_model_calls': 0, 'planned_units': len(units)}
    c.save(c.RUN / 'generation_checks.json', record)
    print(json.dumps(record))
    assert record['passed']


if __name__ == '__main__':
    main()
