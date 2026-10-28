#!/usr/bin/env python3
"""Prepared command-contract checks; no subprocess, GPU or scientific execution."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from e1_d2a5_preflight import command, LIMITS


def main():
    for n, z in ((64, 4096), (128, 8192)):
        for steps in (100000, 1000000):
            argv = command(Path('/preserved/semiflexible'), Path('/evidence/run'), n, steps)
            assert len(argv[1:]) % 2 == 0
            pairs = list(zip(argv[1::2], argv[2::2]))
            flags = dict(pairs)
            assert len(flags) == len(pairs)
            for key, value in {'--springs': str(n), '--chains': '256', '--slip-count': str(z),
                               '--steps': str(steps), '--sample': str(steps), '--dt': '.0001',
                               '--kappa': '10', '--kb': '30', '--b0': '1', '--kbt': '1',
                               '--zeta': '1', '--slip-ms2': '5', '--hop-rate': '100',
                               '--end-renewal': '1', '--stress-mode': 'off',
                               '--dynamics': '1', '--dynamics-stride': '100'}.items():
                assert flags[key] == value, key
            assert flags['--equilibrium-steps'] == flags['--equilibrium-snapshots']
            assert flags['--output'] == '/evidence/run/output'
    assert LIMITS['aggregate_seconds'] > 2*LIMITS['per_run_seconds']
    assert LIMITS['aggregate_output_bytes'] > 2*LIMITS['per_run_output_bytes']


if __name__ == '__main__':
    main()
