#!/usr/bin/env python3
"""Compare ordinary (non-diagnostic) preprocessed source using the production compiler."""
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ASSOC = REPO / 'examples/KG_Assoc'
START = 'b8f518d49c9b00f7d957bc42fcaf0a34a9317c82'
command = shlex.split(subprocess.check_output(
    ['make', '-n', '-B', 'kg_assoc_stars'], cwd=ASSOC, text=True).strip())
source_index = command.index('kg_assoc_stars.cu')
output_index = command.index('-o')
del command[output_index:output_index + 2]
command.remove('-lz')
# Freeze only build timestamps for this comparison; production builds keep actual timestamps.
command.extend(['-E', '-I' + str(ASSOC), '-D__TIME__="00:00:00"',
                '-D__DATE__="Oct 16 2026"'])
original = subprocess.check_output(['git', 'show', START + ':examples/KG_Assoc/kg_assoc_stars.cu'], cwd=REPO)
current = (ASSOC / 'kg_assoc_stars.cu').read_bytes()
results = []
with tempfile.TemporaryDirectory(prefix='readback_ordinary_') as temporary:
    source = Path(temporary) / 'ordinary.cu'
    command[source_index] = str(source)
    for content in (original, current):
        source.write_bytes(content)
        output = subprocess.check_output(command, cwd=ASSOC, text=True)
        lines = [line for line in output.splitlines() if not re.match(r'^\s*#\s*(?:line\s+)?\d', line)]
        normalized = ' '.join(' '.join(lines).split())
        results.append(hashlib.sha256(normalized.encode()).hexdigest())
assert results[0] == results[1], 'ordinary preprocessed source changed'
print(json.dumps(dict(ordinary_preprocessed_source_unchanged=True, normalized_sha256=results,
                      command=command, GPU_calls=0), indent=2))
