"""One bounded, source-derived initial translation shared by all repair methods."""
from __future__ import annotations

import ast
from dataclasses import replace
import json
from pathlib import Path

from repository_bootstrap import parse_files


def units_for(source: Path):
    files = {p.relative_to(source).as_posix(): p for p in sorted(source.rglob('*.py'))}
    modules = {name[:-3].replace('/', '.').removesuffix('.__init__'): name for name in files}
    dependencies = {}
    for name, path in files.items():
        imports = set()
        package = name[:-3].replace('/', '.').split('.')[:-1]
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                prefix = package[:len(package) - node.level + 1] if node.level else []
                module = '.'.join(prefix + ([node.module] if node.module else []))
                imports.add(module)
                imports.update(module + '.' + alias.name for alias in node.names)
        dependencies[name] = sorted({modules[v] for v in imports if v in modules and modules[v] != name})
    order, visited, active = [], set(), set()
    def visit(name):
        if name in visited or name in active:
            return
        active.add(name)
        for dep in dependencies[name]:
            visit(dep)
        active.remove(name)
        visited.add(name)
        if files[name].read_text().strip():
            order.append(name)
    for name in files:
        visit(name)
    units = [{'files': [name], 'dependencies': dependencies[name]} for name in order]
    units.append({'files': ['parameter_map.json', 'requirements.txt', 'README.md'],
                  'dependencies': [name for name in order if not name.startswith('tests/')]})
    return units


def translate(agent, workspace, contract, save, folder):
    """Syntax/format feedback only; no target evaluation or reference outputs."""
    source, target = workspace / 'source', workspace / 'target'
    units = units_for(source)
    states = {name: 'copied_source' for unit in units for name in unit['files']}
    rows = []
    save(folder / 'plan.json', {'units': units, 'config': agent.config.__dict__,
         'per_unit_calls': 2, 'selection': 'first syntactically valid response; no semantic evaluation'})
    original = agent.config
    try:
        for index, unit in enumerate(units, 1):
            if agent._budget_status():
                break
            payload = {'public_task': contract, 'files_to_generate': unit['files'],
                'source_files': {name: (source / name).read_text() for name in unit['files'] if (source / name).exists()},
                'file_generation_states': states,
                'source_dependency_interfaces': {name: (source / name).read_text() for name in unit['dependencies']},
                'current_dependency_files': {name: (target / name).read_text() for name in unit['dependencies']},
                'output_rule': 'Return JSON {"files":{"path":"complete file contents"}} for exactly files_to_generate. Preserve public interfaces and source behavior. Include no Markdown or commentary.'}
            if 'parameter_map.json' not in unit['files']:
                payload['public_task'] = {k: v for k, v in contract.items() if k not in ('source_parameter_metadata', 'public_test_initializations')}
                if any(name.startswith('tests/') for name in unit['files']):
                    payload['public_test_initializations'] = contract.get('public_test_initializations', [])
            messages = [{'role': 'system', 'content': 'Translate the requested repository unit to the native target framework. Maintain compatibility with the public source contract and generated dependencies. Generate complete files in JSON.'},
                        {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}]
            row = {'unit': index, 'files': unit['files'], 'calls': [], 'status': 'unattempted'}
            for trial in range(2):
                if agent._budget_status():
                    break
                response = agent.complete(messages, stage='shared_translation', attempt=index)
                choice = response['choices'][0]
                row['calls'].append(agent.calls)
                try:
                    generated = parse_files(response, unit['files'])
                    for name, contents in generated.items():
                        destination = target / name
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_text(contents)
                        states[name] = 'generated'
                    row['status'] = 'generated'
                    break
                except (ValueError, KeyError, TypeError, SyntaxError) as exc:
                    row.update(status='generation_failed', error=str(exc))
                    for name in unit['files']:
                        states[name] = 'generation_failed'
                    message = {k: v for k, v in choice['message'].items() if k in ('role', 'content', 'reasoning_content')}
                    message['role'] = 'assistant'
                    messages.extend([message, {'role': 'user', 'content': 'The files were not applied. Format/syntax validation: ' + str(exc) + '. Return a complete JSON files object for this unit.'}])
            rows.append(row)
            save(folder / 'progress.json', {'units': rows, 'file_states': states, 'calls': agent.calls, 'usage': agent.usage()})
    finally:
        agent.config = original
    result = {'status': 'completed', 'units': rows, 'file_states': states, 'planned_units': len(units),
              'unattempted_units': len(units) - len(rows), 'calls': agent.calls, 'usage': agent.usage()}
    save(folder / 'result.json', result)
    return result
