#!/usr/bin/env python3
"""Bounded byte comparison of historical and new binaries (same precision)."""
import subprocess
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix='stage2b1-regression-') as temp:
    outputs = []
    for i, binary in enumerate(sys.argv[1:]):
        out = Path(temp)/str(i)
        subprocess.run([str(Path(binary).resolve()), '--springs', '8', '--chains', '17',
                        '--dt', '.005', '--steps', '76', '--sample', '2', '--equil', '3',
                        '--seed', '620008', '--output-mode', 'stream', '--backend', 'async',
                        '--batch', '7', '--corr-levels', '5', '--corr-slots', '8',
                        '--corr-m', '2', '--output', str(out)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        outputs.append((out/'relaxation.csv').read_bytes())
    assert len(outputs) == 2 and outputs[0] == outputs[1]
print('PASS: Stage 2B and default one-worker relaxation.csv byte-identical')
