"""Apply repository-path integration to an isolated copy of the existing runtime."""
from pathlib import Path
import argparse
import hashlib
import json


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    base=a.root/'autofix/autonomous'
    changes={}
    def modify(name, pairs):
        path=base/name;old=path.read_text();new=old
        for before,after in pairs:
            if before not in new: raise ValueError('Missing patch anchor in '+name+': '+before[:80])
            new=new.replace(before,after)
        path.write_text(new)
        changes[name]={'before':hashlib.sha256(old.encode()).hexdigest(),'after':hashlib.sha256(new.encode()).hexdigest()}
    modify('tools.py',[
        ('and parts[0] in {"torch4ms", "scratch_tests"}\n            and path.endswith(".py")',
         'and ((parts[0] in {"torch4ms", "scratch_tests"} and path.endswith(".py")) or (parts[0] in {"source", "target"} and (PurePosixPath(path).suffix in {".py", ".json", ".md", ".txt", ".ipynb", ".yaml", ".yml", ".toml"} or parts[-1] == "LICENSE")))'),
        ('if write and value in {"source.py", "task.json"}:','if write and (value in {"source.py", "task.json"} or parts[0] == "source"):'),
        ('for directory in ("torch4ms", "scratch_tests"):', 'for directory in ("torch4ms", "scratch_tests", "source", "target"):'),
        ('if name.endswith(".py") and not name.startswith(".")', 'if (name.endswith(".py") or directory in {"source", "target"}) and not name.startswith(".")'),
        ('not in {"scratch_tests", "torch4ms"}', 'not in {"scratch_tests", "torch4ms", "target"}'),
        ('relative = path.relative_to(self.root).as_posix()\n                try:', 'relative = path.relative_to(self.root).as_posix()\n                if path.suffix != ".py":\n                    continue\n                try:'),
        ('candidate.py, torch4ms/**/*.py and scratch_tests/**/*.py are repairable.', 'candidate.py, torch4ms/**/*.py, target/**/* and scratch_tests/**/*.py are repairable.'),
        ('New files may be created under torch4ms/ or scratch_tests/.', 'New files may be created under target/, torch4ms/ or scratch_tests/. source/ and task.json are immutable.'),
        ('source.py may be available as an additional reference.', 'source/ contains the immutable full repository when provided; source.py may also be available.')
    ])
    # Replace only the declared target contract; retain verifier, handoff, and repair policy.
    modify('agent.py',[
        ('class AutonomousAgent:\n', 'class AutonomousAgent:\n    def _repository_prompt(self, prompt):\n        if (self.tools.root / "source").is_dir():\n            prompt = prompt.replace("torch4ms/MindSpore for\\nthis task", "the native framework declared in task.json")\n            prompt += "\\nFor this repository task, source/ is immutable and target/ contains the complete editable target repository. Read task.json for the public interfaces and acceptance contract.\\n"\n        return prompt\n\n'),
        ('system_prompt = _evidence_prompt(system_prompt)\n', 'system_prompt = _evidence_prompt(system_prompt)\n        system_prompt = self._repository_prompt(system_prompt)\n'),
        ('fixer_prompt = _evidence_prompt(fixer_prompt)\n', 'fixer_prompt = _evidence_prompt(fixer_prompt)\n        fixer_prompt = self._repository_prompt(fixer_prompt)\n')
        ,('item["path"].startswith("torch4ms/")', 'item["path"].startswith(("torch4ms/", "target/"))')
        ,('elif name == "run_test" and production_edited:', 'elif name in {"run_test", "checkpoint_unit"} and production_edited:')
    ])
    modify('baselines.py',[
        ('Their public paths are source.py and candidate.py.', 'Their paths are declared in task.json (source_entry and target_entry), defaulting to source.py and candidate.py. The full source/ and target/ repositories are also available when supplied.'),
        ('run_test. candidate.py and torch4ms are editable.', 'run_test. candidate.py, torch4ms and target/ are editable; source/ and task.json are immutable.'),
        ('source = self.agent.tools.execute("read", {"path": "source.py"}, readonly=True)', 'contract = json.loads((root / "task.json").read_text())\n        source_path = contract.get("source_entry", "source.py")\n        target_path = contract.get("target_entry", "candidate.py")\n        source = self.agent.tools.execute("read", {"path": source_path}, readonly=True)'),
        ('target = self.agent.tools.execute("read", {"path": "candidate.py"}, readonly=True)', 'target = self.agent.tools.execute("read", {"path": target_path}, readonly=True)'),
        ('"source_path": "source.py", "target_path": "candidate.py",', '"source_path": source_path, "target_path": target_path,'),
        ('(root / "source.py").read_text', '(root / source_path).read_text'),
        ('(root / "candidate.py").read_text', '(root / target_path).read_text'),
        ('if not (self.agent.tools.root / "source.py").is_file():', 'if not (self.agent.tools.root / json.loads((self.agent.tools.root / "task.json").read_text()).get("source_entry", "source.py")).is_file():'),
        ('item["path"].startswith("torch4ms/")', 'item["path"].startswith(("torch4ms/", "target/"))'),
        ('complete genuine public source.py and candidate.py modules', 'complete declared public source/target entry modules, with full repository tool access')
    ])
    modify('swe_upstream.py',[
        ('self.target_python = Path(target_python).resolve()', 'self.target_python = Path(target_python).absolute()'),
        ('paths += sorted((root / "torch4ms").rglob("*.py"))', 'paths += sorted((root / "torch4ms").rglob("*.py"))\n    paths += sorted(p for p in (root / "target").rglob("*") if p.is_file() and "__pycache__" not in p.parts)'),
        ('if not (root / "candidate.py").is_file() or not (root / "task.json").is_file():', 'if not ((root / "candidate.py").is_file() or (root / "target/project.py").is_file()) or not (root / "task.json").is_file():'),
        ('for name in ("torch4ms", "scratch_tests"):', 'for name in ("torch4ms", "scratch_tests", "source", "target"):'),
        ('("source.py", "candidate.py", "task.json", "torch4ms", "scratch_tests")', '("source.py", "candidate.py", "task.json", "torch4ms", "scratch_tests", "source", "target")'),
        ('"has_source": (self.root / "source.py").exists(),', '"has_source": (self.root / "source.py").exists() or (self.root / "source").exists(),\n                  "repository_task": (self.root / "target").is_dir(),'),
        ('writes = [str(self.private), str(self.root / "candidate.py"),', 'writes = [str(self.private), str(self.root / "target"), str(self.root / "candidate.py"),'),
        ('contract += ("source.py and task.json define intended behavior. " if config["has_source"] else', 'contract += (("source/ and task.json define intended behavior. " if config.get("repository_task") else "source.py and task.json define intended behavior. ") if config["has_source"] else'),
        ('problem = (contract + "candidate.py and torch4ms are editable, while source.py and task.json are immutable. "', 'problem = (contract + ("target/ is the editable complete repository; source/ and task.json are immutable. " if config.get("repository_task") else "candidate.py and torch4ms are editable, while source.py and task.json are immutable. ") +')
    ])
    modify('sandbox.py',[
        ('return [str(python.parent.parent), "/usr",', 'return [str(python.parent.parent), str(python.resolve().parent.parent), "/usr",')
    ])
    (a.root/'repository_runtime_integration.json').write_text(json.dumps(changes,indent=2))
    print(json.dumps(changes,indent=2))


if __name__=='__main__':main()
