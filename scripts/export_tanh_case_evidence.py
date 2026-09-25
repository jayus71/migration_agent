"""Export the audited saved Tanh repair case to a self-contained local folder."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'tmp/experiment-addition-review/case-evidence'
AUDIT = ROOT / 'docs/review-evidence/tanh-case-20260925'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    assert sha(source) == sha(destination), destination


ANSWERS = '''# Tanh 案例证据：逐项填写【待核】

本包来自已保存的正式自然翻译修复记录，未运行新实验。先读本文件，再按相对路径查看原始证据。内部任务号、配置名、远端路径只用于核查，不应写进论文。

## 1. 是不是表2(a)的五个失败程序之一？

是。模型是 **AutoencoderHead，自编码器式分类模型**，对应自然翻译集合的 `task_008`、原始来源 `I-08 / autoencoder_head.py`。编码器为 `Linear(15,10) → Tanh → Linear(10,4)`，随后有decoder和分类head。初始执行成功但完整数值验收失败，属于表2(a)的五个初始失败程序。LaDiM当前主表配置最终修好其中四个，本例是这四个之一。它来自已保存的初译，原来源审计记录 `no_fault_injection=true`。

冻结的十例任务中，初始验收失败的是002、003、007、008、009。源代码SHA-256为 `9147733310cb4f26db4f475824fccc37e7db96bbaef62faf35e1787e2728ab9e`。

证据：`code/source.py` 第5–11行；`provenance/frozen_case_selection.json`；`provenance/pool_audit.json` 的I-08条目；`paper_context/TABLE_natural_repairs.tex`；`paper_context/experiments.tex` 中 `tab:repair-results`。完整冻结汇总在 `provenance/recovery_final.json` 与 `provenance/autonomous_recovery_final.json`。

## 2. 原来的functional_tanh如何写、为什么断梯度、改了哪里？

**修复前高层 `functional_tanh` 不存在。** 不是把它的错误函数体改正确，而是在支持库 `torch4ms/ops/mtorch.py` 中新增高层映射及注册。低层 `aten.tanh` 原本已经存在：`code/initial/torch4ms/ops/mten.py` 第277–279行和 `maten.py` 第457–459行均为 `_aten_tanh(x): return ops.tanh(x)`。

高层 `torch.tanh` / `torch.nn.functional.tanh` 找不到注册时，`XLAFunctionMode.__torch_function__` 捕获 `OperatorNotFound`，通过 `ms2t_copy` 把MindSpore张量复制为PyTorch张量，然后执行原生PyTorch函数。数值被保留，但MindSpore反向图在Tanh处断开，导致前一层参数梯度为零。代码位置见 `code/initial/torch4ms/tensor.py` 第883–887、899–920行，尤其905、913、918行。

完整新增补丁为：

```python
@register_function(torch.tanh)
@register_function(torch.nn.functional.tanh)
def functional_tanh(input):
    return mops.tanh(input)
```

它插在原ReLU注册之前，最终文件 `code/ladim_final/torch4ms/ops/mtorch.py` 第1009–1012行。只有这个生产文件发生变化；`candidate.py`、源程序和其他支持库文件未变。因此单看最终candidate无法看到修复，必须连同支持库查看。图中两行只是函数实现节选，两个装饰器是完整补丁的重要组成部分。

证据：`audit/repair.patch`；`key_events/ladim_call22_edit.json`；`key_events/ladim_call17_test.json`。第17次测试返回：native Tanh输入梯度绝对值之和4.894132；dispatched Tanh为0；ReLU=5、Sigmoid=2.140072、乘法=24。

## 3. 修复前Linear 1梯度、loss差多少？

图中Linear 1对应 `encoder.0`。公开seed 42的weight和bias两个梯度张量的范数均为 **0.0**；源程序对应范数分别为0.3422238528728485、0.10949636250734329。它们的梯度L2差分别等于源范数。之后六个参数张量的梯度L2差均不超过6.16×10⁻⁷。

| 指标，公开seed 42 | 修复前 | 修复后 |
| --- | ---: | ---: |
| loss绝对差 | 1.430511474609375e-6 | 1.430511474609375e-6 |
| 梯度向量L2差 | 0.35931411385536194 | 1.0120579645445105e-6 |
| 梯度范数绝对差 | 0.04596114158630371 | 0.0 |
| 参数更新相对L2差 | 0.7711267081348738 | 6.423932404404612e-6 |

验收阈值依次为loss 0.02、梯度向量0.05、梯度范数0.05、更新0.03。因此本例的梯度范数差尚未越阈，但梯度向量与更新检查失败。第一层更新不是严格零：weight更新范数1.8868575352826156e-5，与AdamW权重衰减一致。

证据：`raw/task_008/ladim/result.json` 的 `initial.observation` 与 `final.observation`；同内容也在 `audit/summary.json`。逐参数值见 `gradient_vector_comparison.parameters`；原始成对报告见 `raw/task_008/ladim/evidence/measurement_0001/paired_report.json`。最终公开与1042、2042确认seed均通过；确认值在 `result.json → attempts[1].confirmation`。

## 4. 第17、22、23次调用、提交次数与1.488M范围

| 调用 | 实际动作 | 累计token | 原始工具证据 |
| ---: | --- | ---: | --- |
| 17 | 执行此前写好的activation梯度测试，工具成功返回上述Tanh对比结果 | 735,675 | `key_events/ladim_call17_test.json` |
| 22 | 编辑支持库，新增Tanh高层映射及两个注册装饰器 | 1,258,998 | `key_events/ladim_call22_edit.json` |
| 23 | 运行公开验收，全部检查通过 | 1,384,401 | `key_events/ladim_call23_public_test.json` |
| 24 | 最终报告，随后进行外部公开/确认seed验收 | 1,488,495 | `key_events/ladim_call24_response.json` 与最终result |

**两次外部提交，第2次被接受。** 第1次为仅调查阶段，没有生产修改，验收失败；第2次有上述补丁，三个seed通过。第8次调用已经提出Tanh边界假说，但当时尚未运行针对性测试，不应称第8次已实证精确注册根因。

1.488M是1,488,495 token四舍五入后的数值，**不含初始翻译生成**。它包括本例完整调查、失败阶段、编辑、验证请求与最终报告的所有LLM输入和输出；其中input=1,449,988、output=38,507，共24次调用。逐次账见 `audit/calls.csv`。

日志中的第2次 `stage.status=invalid_final` 是最终输出格式状态；实际代码的 `evaluation.accepted`、确认seed及任务级 `accepted` 均为true，勿将它误当修复失败。完整最终验收以result中的数值检查为准。

## 5. baseline预算、改动与是否注意到Tanh

| 方法 | 调用 | 总token | 生产代码改动 | 最终结果 |
| --- | ---: | ---: | --- | --- |
| LaDiM | 24 | 1,488,495 | mtorch.py新增映射 | 通过 |
| SWE-agent | 40 | 1,606,058 | 无 | 预算耗尽，未修复 |
| MatchFixAgent | 40 | 2,340,608 | 无 | 预算耗尽，未修复 |

两个baseline都用满40次调用，均为 `call_budget_exhausted`；各自最终候选和44个生产代码文件与初始版本逐字一致，`changed_files=[]`。调查期间创建/运行的scratch测试不属于生产补丁，工具请求与结果保存在各自agent日志。

**两者都注意到了Tanh，不能写它们没找到问题。** SWE-agent第27次响应已描述Linear+Tanh测试中上游梯度为零；第35次响应报告Tanh为零而ReLU/Sigmoid正常；第38次分析到缺少高层名称映射及ms2t_copy回退；第39次讨论注册torch.tanh的修复方法，但第40次仍在检查源码。MatchFixAgent第21次分析前层零梯度、第27次怀疑高层注册缺失、第34次讨论OperatorNotFound后的原生复制回退，第37/38次提出同样注册方案，第40次仍在读源码。以上是可核查的记录节点，不作为统一判据下的“首次定位”排名。

对应原始响应已复制到 `key_events/`：`swe_call27_response.json`、`swe_call35_response.json`、`swe_call38_response.json`、`swe_call39_response.json`、`swe_call40_response.json`；以及 `matchfix_call21/27/34/37/38/40_response.json`。描述主要位于 `choices[0].message.reasoning_content`，实际动作位于 `tool_calls`；这些是实验模型保存的记录，须以工具执行与最终代码确认实际完成了什么。完整上下文在 `raw/task_008/<method>/evidence/agent/`。

三个方法的源程序、任务配置、44个初始代码文件和初始观测相同。这里比较从相同异常观测到完成修复的调用/token成本，不比较首次检测速度。记录墙钟时间分别为LaDiM 508.957秒、SWE-agent 491.591秒、MatchFixAgent 344.905秒，因此本例没有墙钟加速优势。

## 文件入口与完整性

- `code/source.py`、`code/task.json`：不可变源程序与公共配置。
- `code/initial/`、`code/ladim_final/`：初始和LaDiM最终candidate及支持库，均为保存字节的原样复制。
- `raw/task_008/ladim/`、`swe_native_isolated/`、`matchfix_full_orchestration/`：三种方法完整下载证据，包括result、各次请求/响应、工具记录、measurement、初始/最终快照。
- `key_events/`：上文涉及的关键节点副本。
- `audit/`：数值总结、104次调用账、补丁、工具证据及原来源哈希。历史来源清单还包含筛选时的task_009；本包只导出task_008，其精确原始文件清单在 `provenance/raw_source_manifest.json`。
- `provenance/`：正式结果选择、表2(a)集合对应和初始无注入来源。
- `paper_context/`：主文表与相关实验章节的当前源码，用于定位表2(a)。
- `figure/`：最新PNG/SVG/PDF及图形生成脚本，沿用已审计数字。生成脚本保留原仓库路径，需要原仓库环境才能重画；此处图形资产可直接查看。
- `MANIFEST.json`：本包每个文件的SHA-256和字节数；`verify_manifest.py`可用标准Python复核，不运行训练或模型。

本包的candidate与支持库用于核查；重跑训练仍需原MindSpore/torch4ms运行环境。若另一工具无法访问D盘，可直接提供本包README和关键文件，或把旁边的ZIP附给它。
'''


VERIFY = '''import hashlib, json
from pathlib import Path
root = Path(__file__).resolve().parent
entries = json.loads((root / 'MANIFEST.json').read_text(encoding='utf-8'))['files']
for entry in entries:
    path = root / entry['path']
    assert path.stat().st_size == entry['size'], entry['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], entry['path']
print(f'Verified {len(entries)} files; no experiment was run.')
'''


def finalize_bundle(destination, raw_files, commit):
    """Write the evidence index, verify every file, and create a verified ZIP."""
    archive = destination.with_name(destination.name + '.zip')
    entry_readme = destination.parent / 'README_先读.md'
    if archive.exists() or entry_readme.exists():
        raise FileExistsError('Refusing to replace an existing archive or entry README')
    (destination / 'README_五项核对.md').write_text(ANSWERS, encoding='utf-8')
    (destination / 'verify_manifest.py').write_text(VERIFY, encoding='utf-8')
    files = [
        {'path': str(p.relative_to(destination)), 'size': p.stat().st_size, 'sha256': sha(p)}
        for p in sorted(destination.rglob('*'))
        if p.is_file() and p != destination / 'MANIFEST.json'
    ]
    write_json(destination / 'MANIFEST.json', {
        'repository_commit': commit, 'raw_files_verified': raw_files, 'files': files,
    })
    subprocess.run([sys.executable, str(destination / 'verify_manifest.py')], check=True)
    members = sorted(p for p in destination.rglob('*') if p.is_file())
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6, strict_timestamps=False) as z:
        for p in members:
            z.write(p, arcname=str(p.relative_to(destination.parent)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.infolist()) == len(members)
        for p in members:
            data = z.read(str(p.relative_to(destination.parent)))
            assert len(data) == p.stat().st_size and hashlib.sha256(data).hexdigest() == sha(p), p
    result = {
        'directory': str(destination), 'raw_files': raw_files,
        'files_in_manifest': len(files), 'files_including_manifest': len(members),
        'total_bytes': sum(p.stat().st_size for p in members),
        'all_hashes_verified': True, 'repository_commit': commit,
        'zip_path': str(archive), 'zip_bytes': archive.stat().st_size,
        'zip_sha256': sha(archive), 'zip_crc_and_member_hashes_verified': True,
    }
    entry_readme.write_text(
        '# Tanh 案例材料入口\n\n'
        '先看 [五项核对说明](tanh-case-evidence/README_五项核对.md)：已逐项回答模型归属、原始缺陷与补丁、修复前后测量、调用节点与成本，以及两种基线的调查和终态，并列出对应原始文件。\n\n'
        '- [完整证据目录](tanh-case-evidence/)：原始运行日志、candidate与支持库、源程序、任务配置、验收报告、调用账、图及论文上下文。\n'
        '- [完整压缩包](tanh-case-evidence.zip)：与证据目录逐文件一致，适合上传给无法读取D盘的工具。\n'
        '- [完整性清单](tanh-case-evidence/MANIFEST.json)：各文件SHA-256；在包内运行 `python verify_manifest.py` 可复核。\n\n'
        f'共{raw_files}个原始证据文件，整理后含清单共{len(members)}个文件。复制文件SHA-256、ZIP CRC及ZIP内每个文件的SHA-256均已核对。\n\n'
        '两处关键澄清：修复前缺少高层Tanh注册；两种基线都分析到了Tanh，但40次调用后未落实生产代码补丁。LaDiM的1,488,495 token不包含初始翻译。\n\n'
        '材料来自保存的实验记录，本次只整理和核查，没有运行新实验或修改论文。\n',
        encoding='utf-8',
    )
    write_json(destination.parent / 'export_verification.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    destination = args.destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    source_manifest = read(RAW / 'manifest.json') + read(RAW / 'workspace_manifest.json')
    case_manifest = [e for e in source_manifest if e['file'].startswith('task_008/')]
    assert set(e['file'] for e in case_manifest) == {str(p.relative_to(RAW)) for p in (RAW / 'task_008').rglob('*') if p.is_file()}
    for e in case_manifest:
        p = RAW / e['file']
        assert p.stat().st_size == e['size'] and sha(p) == e['sha256'], e['file']
        copy(p, destination / 'raw' / e['file'])
    for p in AUDIT.iterdir():
        if p.is_file():
            copy(p, destination / 'audit' / p.name)
    base = RAW / 'task_008/ladim'
    for name in ['source.py', 'task.json']:
        copy(base / 'workspace' / name, destination / 'code' / name)
    for source, target in [('initial_code', 'initial'), ('final_code', 'ladim_final')]:
        for p in (base / 'evidence' / source).rglob('*'):
            if p.is_file():
                copy(p, destination / 'code' / target / p.relative_to(base / 'evidence' / source))
    event_names = {'event_00073_tool.json': 'ladim_call17_test.json', 'event_00094_tool.json': 'ladim_call22_edit.json', 'event_00097_tool.json': 'ladim_call23_public_test.json'}
    for source, target in event_names.items():
        copy(base / 'evidence/agent' / source, destination / 'key_events' / target)
    for method, short, calls in [('ladim', 'ladim', [8, 17, 22, 23, 24]), ('swe_native_isolated', 'swe', [27, 35, 38, 39, 40]), ('matchfix_full_orchestration', 'matchfix', [21, 27, 34, 37, 38, 40])]:
        for call in calls:
            copy(RAW / 'task_008' / method / 'evidence/agent' / f'call_{call:04d}_response.json', destination / 'key_events' / f'{short}_call{call}_response.json')
    inputs = {
        'output/maintext-ablations-20260918/recovery_final.json': 'provenance/recovery_final.json',
        'output/autonomous-verifier-20260917/autonomous_recovery_final.json': 'provenance/autonomous_recovery_final.json',
        'output/maintext-results-20260918/evidence_index.json': 'provenance/evidence_index.json',
        'data/experiments/09_experiment_I_real_translation/runs_real_core_v3/pool_audit.json': 'provenance/pool_audit.json',
        'sections/experiments.tex': 'paper_context/experiments.tex',
        'sections/supplementary_experiments.tex': 'paper_context/supplementary_experiments.tex',
        'figures/TABLE_natural_repairs.tex': 'paper_context/TABLE_natural_repairs.tex',
        'figures/make_tanh_repair_case.py': 'figure/make_tanh_repair_case.py',
    }
    for source, target in inputs.items():
        copy(ROOT / source, destination / target)
    for p in (ROOT / 'figures/tanh-repair-case').iterdir():
        if p.is_file():
            copy(p, destination / 'figure' / p.name)
    frozen = read(ROOT / 'output/maintext-ablations-20260918/recovery_final.json')
    group = next(g for g in frozen['groups'] if g.get('study') == 'natural10_v3' and g.get('variant') == 'without_edit_format_feedback')
    selection = {'main_method_group': group, 'task': 'task_008', 'initially_failed': [r['task'] for r in group['rows'] if not r['initially_accepted']], 'table_label': 'tab:repair-results(a)', 'source_input_hashes': {source: sha(ROOT / source) for source in inputs}}
    assert selection['initially_failed'] == ['task_002', 'task_003', 'task_007', 'task_008', 'task_009']
    assert next(r for r in group['rows'] if r['task'] == 'task_008')['accepted']
    write_json(destination / 'provenance/frozen_case_selection.json', selection)
    write_json(destination / 'provenance/raw_source_manifest.json', case_manifest)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    result = finalize_bundle(destination, len(case_manifest), commit)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
