#!/usr/bin/env python3
"""Phase B build/read-only preflight; separate explicit Phase B approval required."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import sys

import e1_d14_phase_b as spec
import e1_d14_phase_b_auth as auth
from e1_d13_reuse import bind
from e1_d1_pilot import require

# Private binding keeps frozen Phase A globals, code and evidence untouched.
definition=importlib.util.spec_from_file_location('_d14_accepted_orchestration',spec.PROJECT/'e1_d13_phase_a_runner.py')
accepted=importlib.util.module_from_spec(definition);definition.loader.exec_module(accepted)
accepted.spec=spec;accepted.auth=auth
accepted.shared=bind('runner',spec);accepted.shared.auth=auth.base
accepted._machine=accepted.shared.machine
accepted.shared.machine=accepted.machine
shared=accepted.shared


def preflight(args):
    summary,*rest=accepted.preflight(args)
    summary['execution_flag_required']='--authorize-phase-b-execution'
    summary['phase']='B'
    return summary,*rest


def execute(args,summary,manifest,build,approval,limits):
    require(args.authorize_phase_b_execution is True,'explicit Phase B execution flag required')
    # Internal compatibility field only; the Phase A flag is absent from this CLI.
    bound=copy.copy(args);bound.authorize_phase_a_execution=True
    return accepted.execute(bound,summary,manifest,build,approval,limits)


def main():
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='action')
    b=subs.add_parser('build',help='fresh pinned-source double compilation; no trajectories')
    for name in ('source-tree','build-root','cuda-home'):b.add_argument('--'+name,type=Path,required=True)
    b.add_argument('--arch',required=True);b.add_argument('--cxx',type=Path,default=Path('/usr/bin/g++'))
    p=subs.add_parser('preflight',help='read-only unless explicitly approved for Phase B')
    for name in ('build-receipt','approval','output-root'):p.add_argument('--'+name,type=Path)
    for name in ('build-sha256','approval-sha256','gpu-uuid'):p.add_argument('--'+name)
    p.add_argument('--authorize-phase-b-execution',action='store_true')
    for child in (b,p):
        child.add_argument('--manifest',type=Path,default=spec.CONFIG/'manifest.json')
        child.add_argument('--manifest-sha256',default=(spec.CONFIG/'manifest.sha256').read_text().split()[0])
    if len(sys.argv)==1:sys.argv.append('preflight')
    args=parser.parse_args()
    def stop(signum,frame):raise KeyboardInterrupt('signal '+str(signum))
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGHUP,stop)
    try:
        if args.action=='build':result=shared.build(args)
        elif args.action=='preflight':
            summary,manifest,build,approval,limits=preflight(args);print(json.dumps(summary,indent=2,allow_nan=False),flush=True)
            if not args.authorize_phase_b_execution:return
            require(not summary['blockers'] and approval is not None,'Phase B preflight blocked')
            with shared.gpu_lock(approval['gpu_uuid']):result=execute(args,summary,manifest,build,approval,limits)
        else:parser.print_help();return
        print(json.dumps(result,indent=2,allow_nan=False))
    except KeyboardInterrupt as error:parser.exit(130,f'Phase B interrupted; evidence preserved: {error}\n')
    except (OSError,ValueError,KeyError,TypeError,AssertionError,subprocess.SubprocessError) as error:
        parser.exit(1,f'Phase B refused: {error}\n')


if __name__=='__main__':main()
