#!/usr/bin/env python3
"""Prepared lightweight synthetic CPU checks; no GPU, build, historical evidence or pilot."""
import argparse
import copy
import csv
from fractions import Fraction
from pathlib import Path
import sys
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
import e1_d17_spec as spec
import e1_d17_host as host
import e1_d17_analyze as analysis
import numpy as np


def reject(action):
    try:
        action()
    except (ValueError,KeyError,AssertionError,FileNotFoundError):
        return
    raise AssertionError('malformed or unauthorized request accepted')


def csv_fixture(out):
    path = out/'frame.csv'
    header = ['step','time','chain','value']
    def write(rows, columns=header):
        with path.open('w',newline='') as stream:
            w = csv.writer(stream)
            w.writerow(columns)
            w.writerows(rows)
    for dt in ('0.00025','0.0001','0.00005'):
        end = spec.exact_step('.5',dt)
        good = [[0,0,0,1],[0,0,1,2],[end,.5,0,3],[end,.5,1,4]]
        write(good)
        assert len(list(spec.frames(path,header,2,[0,end],dt))) == 2
        for bad in (good[:-1],good+[[end+1,.6,0,5]],[[0,0,0,'nan']]+good[1:],
                    [good[0],[0,0,0,2]]+good[2:],good[:2]+[[end,.6,0,3]]+good[3:]):
            write(bad)
            reject(lambda:list(spec.frames(path,header,2,[0,end],dt)))
        write(good,['step','time','chain','bad'])
        reject(lambda:list(spec.frames(path,header,2,[0,end],dt)))


def approval_and_cohort(out, manifest):
    root = out/'synthetic-campaign'
    root.mkdir()
    prepared = dict(candidate=manifest,runs=spec.runs(manifest))
    host.write(root/'manifest.json',prepared)
    host.write(root/'readiness.json',{'synthetic':True})
    host.write(root/'approval-template.json',host.approval_template(root))
    approval = dict(host.approval_template(root),execution_authorized=True,independent_review_reference='SYNTHETIC_ONLY')
    host.write(root/'approval.json',approval)
    assert host.validate_approval(root,root/'approval.json',spec.digest(root/'approval.json')) == approval
    for field,value in (('stage','B'),('stage_b_authorized',True),('execution_authorized',False),
                        ('independent_review_reference',None),('limits',{})):
        host.atomic(root/'approval.json',dict(approval,**{field:value}))
        reject(lambda:host.validate_approval(root,root/'approval.json',spec.digest(root/'approval.json')))
    host.atomic(root/'approval.json',approval)
    reject(lambda:host.validate_approval(root,root/'approval.json','0'*64))
    with patch.object(host.supervisor,'run_process',side_effect=AssertionError('no child allowed')):
        reject(lambda:host.run(root,root/'approval.json',spec.digest(root/'approval.json'),False))
    receipts = {}
    for item in prepared['runs']:
        directory = root/'runs'/item['id']
        directory.mkdir(parents=True)
        host.write(directory/'launch.json',dict(run=item,argv=spec.command(item,root),manifest=spec.file_record(root/'manifest.json')))
        process = dict(status='exited',exit_code=0,wall_seconds=.1,max_rss_bytes=1024)
        host.write(directory/'process.json',process)
        host.write(directory/'receipt.json',dict(run=item,process=process,validation={'synthetic':True},
            stage_wall_seconds=.2,files=spec.snapshot(directory)))
        receipts[item['id']] = spec.file_record(directory/'receipt.json')
    host.write(root/'environment.json',dict(gpu=dict(name='synthetic')))
    host.write(root/'status.json',dict(status='completed_stage_a_not_scientific_acceptance',
        completed_runs=[r['id'] for r in prepared['runs']],wall_seconds=1.))
    complete = dict(receipts=receipts,**{name:spec.file_record(root/(name+'.json')) for name in ('status','manifest','approval','environment')})
    host.write(root/'complete.json',complete)
    completion_sha = spec.digest(root/'complete.json')
    # Build checks are separately specified below; only campaign identity/receipt closure is real here.
    with patch.object(host,'checked',return_value=prepared),patch.object(host,'validate_output',return_value={'synthetic':True}) as validator:
        _,before = host.authenticate(root,completion_sha)
        assert validator.call_count == 24
        target = root/'runs'/prepared['runs'][-1]['id']/'launch.json'
        original = target.read_bytes()
        target.write_bytes(original+b' ')
        reject(lambda:host.authenticate(root,completion_sha))
        target.write_bytes(original)
        assert spec.snapshot(root) == before
        status = spec.load(root/'status.json')
        host.atomic(root/'status.json',dict(status,completed_runs=status['completed_runs'][:-1]))
        altered = dict(complete,status=spec.file_record(root/'status.json'))
        host.atomic(root/'complete.json',altered)
        reject(lambda:host.authenticate(root,spec.digest(root/'complete.json')))
    # Actual build-input hash mismatch is rejected before any historical validator invocation.
    proof,binary = out/'bad-build.json',out/'fake-executable'
    proof.write_text('{}')
    binary.write_text('synthetic-not-executable')
    reject(lambda:host.check_build(proof,'0'*64,binary,manifest))
    synthetic_manifest = dict(manifest,historical_build_sha256=spec.digest(proof),executable=spec.file_record(binary))
    build = dict(source=dict(sha=manifest['source_sha']),binary=dict(file=spec.file_record(binary)))
    with patch.object(host.historical,'validate_build',return_value=build):
        host.check_build(proof,spec.digest(proof),binary,synthetic_manifest)
        binary.write_text('changed synthetic executable')
        reject(lambda:host.check_build(proof,spec.digest(proof),binary,synthetic_manifest))
        binary.write_text('synthetic-not-executable')
        build['source']['sha'] = '0'*40
        reject(lambda:host.check_build(proof,spec.digest(proof),binary,synthetic_manifest))
    proof.write_text('{"changed":true}')
    reject(lambda:host.check_build(proof,synthetic_manifest['historical_build_sha256'],binary,synthetic_manifest))
    host.write(out/'once.json',{})
    reject(lambda:host.write(out/'once.json',{}))


def inference_checks(out, manifest):
    x = analysis.summary([1.,2.,3.,4.])
    np.testing.assert_allclose([x['mean'],x['sd'],x['se']],[2.5,np.sqrt(5/3),np.sqrt(5/3)/2])
    np.testing.assert_allclose(x['loo'],[3.,8/3,7/3,2.])
    assert analysis.summary([1.,1.,1.,1.])['interval'] is None
    assert analysis.summary([0.,0.,0.,0.],bounds=(0.,1.))['interval'][1] > 0
    reject(lambda:analysis.summary([1.,2.,3.]))
    reject(lambda:analysis.summary([1.,2.,3.,float('nan')]))
    difference = analysis.contrast([1.,2.,3.,4.],[4.,5.,6.,7.])
    np.testing.assert_allclose([difference['difference'],difference['df']],[3.,6.])
    assert len(difference['loo']) == 16
    assert analysis.contrast([1.]*4,[2.]*4)['interval'] is None
    refs = analysis.references()
    assert refs['targets']['connector_e2'] == 5 and refs['targets']['connector_e4'] == 125/3
    np.testing.assert_allclose(sum(refs['canonical_law']['pmf']),1)
    assert refs['canonical_law']['mean'] == 8
    full = [(float(tm),{'q':float(tm)}) for tm in range(0,101,2)]
    assert analysis.window(full,'q',manifest['windows']['early']) == dict(value=6.,frames=5,first=2.,last=10.)
    assert analysis.acf_diagnostic([str(tm) for tm,_ in full],[v['q'] for _,v in full],'2')['tau_int'] is None
    runs,data = spec.runs(manifest),{}
    for run in runs:
        scalar = []
        for i in range(201):
            # Fabricated trends/replica variation; no physical or reference draws.
            row = {q:refs['targets'][q]*(1+.001*run['replica'])+.00001*i for q in ('re2','rg2','mean_r2','tangent1')}
            scalar.append((i/2,row))
        keys = ('connector_e2','connector_e4','population_variance') if run['Z'] else ('tangent8','tangent16')
        data[run['id']] = dict(scalar=scalar,
            full=[(float(tm),{q:refs['targets'][q]*(1+.001*run['replica'])+.000001*tm for q in keys}) for tm in range(0,101,2)],
            events=[dict(previous_step=0,interval_time='0',time='0',**{k:'0' for k in host.historical.COUNTERS})],
            bond_histogram=[1/33]*33,process=dict(wall_seconds=.1,max_rss_bytes=1024),
            output_bytes=1024,stage_wall_seconds=.2,
            metadata=dict(integration_seconds=1.,production_wall_seconds=2.,initialization_seconds=.1,
                          final_output_seconds=.1,integration_timer_scope='synthetic'))
    target = out/'synthetic-analysis'
    target.mkdir()
    comparisons,precision = analysis.tables(target,manifest,runs,data,refs)
    assert sum(r['primary_late'] for r in comparisons) == len(precision) == 27
    assert all(r['status'] == 'PILOT_FOR_INDEPENDENT_REVIEW_NO_STAGE_B_AUTHORIZATION' for r in precision)
    analysis.figures(target,comparisons,data,manifest,refs)
    assert len(list(target.glob('*.png'))) == 5


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    out = spec.output_path(parser.parse_args().output)
    out.mkdir(parents=True,exist_ok=False)
    reject(lambda:spec.output_path(spec.BASE))
    reject(lambda:spec.output_path(spec.BASE/'..'/'outside'))
    (out/'link').symlink_to(out,target_is_directory=True)
    reject(lambda:spec.output_path(out/'link'/'nested'))
    manifest = spec.candidate()
    runs = spec.runs(manifest)
    assert len(runs) == len({r['seed'] for r in runs}) == 24
    assert sum(r['steps'] for r in runs) == 27200000
    for run in runs:
        schedule = spec.schedules(manifest)[run['schedule']]
        assert len(schedule) == 51 and [Fraction(s)*Fraction(run['dt']) for s in schedule] == list(map(Fraction,range(0,101,2)))
        argv = spec.command(run,out/'not-created')
        assert argv[argv.index('--hop-rate')+1] == '100'
        assert argv[argv.index('--end-renewal')+1] == ('1' if run['Z'] else '0')
        counts = spec.old_counts(run,schedule,[0,run['steps']])
        assert counts['samples.csv'] == 51456 and counts['equilibrium_sites.csv'] == 430848
    reject(lambda:spec.exact_step('.0001','.00025'))
    # Collision checks only see synthetic metadata roots, never historical evidence.
    audit = out/'audit-fixture'
    audit.mkdir()
    (audit/'old.json').write_text('{"seed":1}')
    assert spec.seed_audit(manifest,[audit],out/'excluded')['status'] == 'NO_MATCHES_IN_DECLARED_SCOPE'
    (audit/'old.json').write_text('{"seed":'+str(runs[0]['seed'])+'}')
    reject(lambda:spec.seed_audit(manifest,[audit],out/'excluded'))
    csv_fixture(out)
    approval_and_cohort(out,manifest)
    inference_checks(out,manifest)
    host.write(out/'PASS.json',dict(status='SYNTHETIC_CPU_CHECKS_PASSED_NOT_SCIENTIFIC_ACCEPTANCE',
        scope='Real schedule/frame/statistical/approval/receipt logic; physical validator and historical build closure mocked in cohort checks. No GPU calls.'))
    print(out)


if __name__ == '__main__':
    main()
