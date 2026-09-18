# Archived evidence for the grouped-query attention code example

`repair_case_evidence.json` records the probes and edited lines used by the
grouped-query attention code example in the manuscript.
It is extracted with `scripts/extract_repair_case_evidence.py` from the original
Fixed50 reports. Each source path and SHA-256 is included in the JSON. Extraction
reads existing results and does not run the LLM or execute candidate programs.

The grouped-query attention case uses NU-07-B with four query heads and two
key/value heads. The first Direct LLM, SWE-agent, and LaDiM candidates restore
execution but retain whole-sequence tiling. Their maximum output difference is
1.0285910367965698. LaDiM's second candidate repeats each head consecutively,
reducing the difference to 9.94652509689331e-7. The probe in
`autofix/faults/core_qwen.py::_probe_only` accepts finite outputs with maximum
absolute difference at most `1e-4`; this differs from the diagnostic studies'
loss threshold. The stated head orders expand the recorded repetition operators analytically.
Their order is not an additional experimental measure.

The case compares the first runnable baseline patches with LaDiM's accepted
second patch. Direct LLM and SWE-agent have no accepted repair in four attempts.
The first patches from all three methods edit only `torch4ms/ops/mtorch.py`.
The snapshot retains all attempts; `probe: null` means no numerical payload was
available after that attempt, and must not be interpreted as zero difference.
