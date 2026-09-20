"""Collect all outcomes and all shared generation costs without selecting runs."""
from repository_timeseries_pilot import RUN,ROOT,read,save,hashes


def main():
    generations=[]
    for folder in [RUN/'translation',RUN/'translation_stages/core',RUN/'translation_stages/examples']:
        p=folder/'response.json'
        if not p.exists():continue
        response=read(p)
        status=read(folder/'status.json')
        previous=read(folder/'previous_adapter_error.json') if (folder/'previous_adapter_error.json').exists() else {}
        generations.append({'path':str(p.relative_to(RUN)),'model':response.get('model'),
          'finish_reason':response['choices'][0].get('finish_reason'),'usage':response.get('usage'),
          'wall_time_seconds':status.get('seconds',0)+previous.get('seconds',0)})
    generation_usage={k:sum(r['usage'].get(k,0) for r in generations if r['usage'])
                      for k in ('prompt_tokens','completion_tokens','total_tokens')}
    rows=[]
    for method in ('initial','ladim','swe','matchfix','ladim_repository','ladim_repository_complete'):
        path=RUN/'conditions'/method/'result.json'
        if not path.exists():continue
        r=read(path)
        notebook_path=RUN/'notebook_audit'/method/'result.json'
        notebook=read(notebook_path) if notebook_path.exists() else None
        snippet_path=RUN/'snippet_audit'/method/'result.json'
        snippets=read(snippet_path) if snippet_path.exists() else None
        completion_path=RUN/'conditions'/method/'completion_result.json'
        completion=read(completion_path) if completion_path.exists() else None
        complete_final=r.get('final',{}) if method=='ladim_repository_complete' else None
        if complete_final:
            entries=complete_final.get('entrypoints',{}).get('entrypoints',{})
            notebook=entries.get('notebook');snippets=entries.get('snippets')
        usage=r.get('usage') or {}
        target=RUN/'conditions'/method/'workspace/target'
        notebook_path=target/'demo-predicting-stock-prices.ipynb'
        notebook_document=read(notebook_path) if notebook_path.exists() else {}
        source_readme=RUN/'source/README.md'
        target_readme=target/'README.md'
        artifact_notes={
            'readme_identical_to_source':target_readme.read_bytes()==source_readme.read_bytes() if target_readme.exists() else None,
            'notebook_code_cells_with_stored_outputs':sum(bool(cell.get('outputs')) for cell in notebook_document.get('cells',[]) if cell.get('cell_type')=='code'),
            'entrypoint_numeric_equivalence':'Core model only; notebook and snippet execution checks do not compare their numerical traces to source.'}
        rows.append({'method':method,'status':r.get('status','evaluated'),
                     'accepted':r['accepted'],
                     'acceptance_protocol':'core plus executed notebook and snippets' if complete_final else 'original core and static coverage',
                     'frozen_acceptance':complete_final.get('core',{}).get('accepted') if complete_final else r['accepted'],
                     'notebook_execution':notebook.get('status') if notebook else 'not_measured',
                     'notebook_error':notebook.get('error') if notebook else None,
                     'snippet_execution':snippets.get('status') if snippets else 'not_measured',
                     'snippet_error':snippets.get('error') if snippets else None,
                     'repair_calls':r.get('calls',0),'repair_usage':r.get('usage'),
                     'shared_generation_calls':len(generations),'shared_generation_usage':generation_usage,
                     'attempts':len(r.get('attempts',[])),'seconds':r.get('seconds'),
                     'end_to_end_total_tokens':usage.get('total_tokens',0)+generation_usage['total_tokens'],
                     'artifact_notes':artifact_notes,
                     'result_path':str(path.relative_to(RUN)),'error':r.get('error'),
                     'complete_protocol_final':complete_final,
                     'entrypoint_completion':None if completion is None else {
                        'status':completion['status'],'accepted':completion.get('accepted'),
                        'cumulative_calls':completion.get('calls'),'cumulative_usage':completion.get('usage'),
                        'note':'Our remaining-budget continuation with additional entrypoint observations. Baselines were not rerun under the added feedback.',
                        'final_entrypoints':completion.get('final',{}).get('entrypoints')}})
    result={'source_repository':'jinglescode/time-series-forecasting-pytorch','target_framework':'native MindSpore',
            'repositories':1,'generations':generations,'physical_generation_usage':generation_usage,'methods':rows,
            'source_unchanged':read(RUN/'manifest.json')['source_hashes']==hashes(RUN/'source'),
            'evidence_root':str(RUN),'implementation_root':str(ROOT)}
    save(RUN/'summary.json',result)
    import json
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
