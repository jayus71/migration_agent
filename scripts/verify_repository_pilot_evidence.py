"""Read-only integrity and cost verification for the repository pilot."""
import hashlib
import importlib.metadata
import json
from repository_timeseries_pilot import RUN,ROOT,read,save,hashes


def main():
    manifest=read(RUN/'manifest.json');freeze=read(RUN/'launch_freeze.json')
    checks={'frozen_source_tree_unchanged':hashes(RUN/'source')==manifest['source_hashes']}
    for name in ('baselines.py','swe_upstream.py','sandbox.py','tools.py'):
        checks['original_integration_unchanged_'+name]=hashlib.sha256((ROOT/'autofix/autonomous'/name).read_bytes()).hexdigest()==freeze['runtime_hashes'][name]
    initial=hashes(RUN/'translation/target')
    for name in ('ladim_repository','ladim_repository_complete'):
        folder=RUN/'conditions'/name
        if (folder/'protocol.json').exists():
            checks[name+'_same_initial_target']=read(folder/'protocol.json')['initial_target_hashes']==initial
    for folder in (RUN/'conditions').iterdir():
        if (folder/'workspace/source').is_dir():checks[folder.name+'_source_immutable']=hashes(folder/'workspace/source')==manifest['source_hashes']
    responses=[]
    for p in RUN.rglob('*response.json'):
        if '/workspace/' in str(p):continue
        try:r=read(p)
        except (ValueError,UnicodeDecodeError):continue
        if isinstance(r,dict) and 'choices' in r and 'usage' in r:
            responses.append({'path':str(p.relative_to(RUN)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                 'usage':r['usage'],'actual_model':r.get('model')})
    environment={}
    for package in ('mindspore','numpy','torch','matplotlib','alpha-vantage'):
        try:environment[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:environment[package]='not installed in controller environment'
    result={'checks':checks,'passed':all(checks.values()),'provider_responses':responses,
             'all_attempts_physical_model_calls':len(responses),
             'all_attempts_physical_tokens':sum(r['usage'].get('total_tokens',0) for r in responses),
             'accounting_scope':'Includes initial exhausted calls, both generation stages, original conditions and all development runs; cumulative continuation usage is not counted twice.',
             'controller_environment':environment}
    save(RUN/'evidence_verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='provider_responses'},indent=2))


if __name__=='__main__':main()
