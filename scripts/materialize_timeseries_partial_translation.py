"""Recover complete file values from a truncated bundle; never repair file contents."""
import json
import re
import shutil
from pathlib import PurePosixPath
from repository_timeseries_pilot import RUN,read,save,hashes,coverage


def complete_members(text):
    match=re.match(r'\s*\{\s*"files"\s*:\s*\{',text)
    if not match:raise ValueError('Expected files object at response start')
    decoder=json.JSONDecoder();pos=match.end();files={}
    while pos<len(text):
        while pos<len(text) and text[pos].isspace():pos+=1
        if pos>=len(text) or text[pos]=='}':break
        try:
            key,end=decoder.raw_decode(text,pos)
            pos=end
            while pos<len(text) and text[pos].isspace():pos+=1
            if text[pos]!=':':raise ValueError('Missing colon')
            pos+=1
            while pos<len(text) and text[pos].isspace():pos+=1
            value,end=decoder.raw_decode(text,pos)
        except (json.JSONDecodeError,IndexError):break
        if not isinstance(key,str) or not isinstance(value,str) or key in files:raise ValueError('Invalid member')
        files[key]=value;pos=end
        while pos<len(text) and text[pos].isspace():pos+=1
        if pos<len(text) and text[pos]==',':pos+=1
        elif pos<len(text) and text[pos]=='}':break
        else:break
    return files,pos


def main():
    response=read(RUN/'translation_stages/examples/response.json')
    assert response['choices'][0]['finish_reason']=='length'
    files,offset=complete_members(response['choices'][0]['message']['content'])
    required={k for k in read(RUN/'manifest.json')['source_hashes'] if k.startswith('step_by_step_code_blocks/') or k in ('demo-predicting-stock-prices.ipynb','README.md')}
    accepted={};ignored=[]
    for name,value in files.items():
        path=PurePosixPath(name)
        if path.is_absolute() or any(x.startswith('.') for x in path.parts):raise ValueError('Invalid response path')
        name=PurePosixPath(*path.parts[1:]).as_posix() if path.parts[0]=='target' else name
        if name not in required:ignored.append(name);continue
        if name in accepted:raise ValueError('Duplicate path')
        accepted[name]=value
    record={'transport_complete':False,'complete_file_values':list(files),'applied_example_files':sorted(accepted),
            'discarded_out_of_stage_paths':ignored,'incomplete_or_missing_example_files':sorted(required-set(accepted)),
            'last_complete_offset':offset,'policy':'Apply complete returned strings only for declared stage paths. Keep prior core unchanged. Unreturned paths retain source files and remain subject to the same final acceptance. No file-content edits or extra model requests.'}
    save(RUN/'partial_translation_extraction.json',record)
    target=RUN/'translation/target'
    shutil.copytree(RUN/'source',target)
    core=RUN/'translation_stages/core/files'
    for name in read(RUN/'translation_stages/core/status.json')['files']:
        shutil.copy2(core/name,target/name)
    for name,value in accepted.items():
        path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value)
    save(RUN/'staged_translation_result.json',{'status':'partial_generated','generation_calls':3,'files':hashes(target),'coverage':coverage(target),'extraction':record})
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
