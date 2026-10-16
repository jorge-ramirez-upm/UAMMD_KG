#!/usr/bin/env python3
"""Read-only audit of the stopped retest; never launches/reinterprets a trajectory."""
import argparse
import csv
import importlib.util
import json
import math
from pathlib import Path
import re
import struct
import sys

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ROOT = REPO / 'examples/KG_Assoc/kg_assoc_100m'
WORK = ROOT / 'aggregate/e2/ea_transfer_diagnostic_retest_20261016_v1'
sys.path.insert(0, str(REPO / 'examples/KG_Assoc/campaign'))
import kg_assoc_e2 as e2
from kg_assoc_e2_readback import represented_position

spec = importlib.util.spec_from_file_location('historical_smoke_analysis',
    HERE.parent / 'e2_ea_transfer_gpu_smoke_20261016/reproduce.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


def float32(value):
    return struct.unpack('f', struct.pack('f', value))[0]


def velocity_audit(serialized, expected, actual):
    """No tolerance: distinguish bad expected evidence from actual loader disagreement."""
    assert all(math.isfinite(x) for x in (*serialized, *expected, *actual))
    represented = [float32(x) for x in serialized]
    return dict(actual_matches_represented=[a == b for a, b in zip(actual, represented)],
        recorded_expected_matches_represented=[a == b for a, b in zip(expected, represented)],
        recorded_expected_matches_serialized=[a == b for a, b in zip(expected, serialized)],
        signed_native_comparison_error=[a-b for a, b in zip(actual, expected)])


def readback_audit(path, parent, pairs, entry):
    lines = path.read_text().splitlines()
    header = '\n'.join(line for line in lines if line.startswith('#') and not line.startswith('# build '))
    fields = dict(re.findall(r'\b(\w+)=([^\s]+)', header))
    for key, expected in dict(system=entry['system']['system_id'],
            branch=entry['lineage']['branch_id'], replica=f"r{entry['replica']:03d}",
            absolute_step='8000000', chemistry_sweep='0', branch_age='0',
            real_bytes='4', rounding_mode='0', cutoff='1.25', strict_rsq_lt='1.5625',
            mapping_valid='1', readback_pass='0', max_position_mic_error='0',
            validation_evidence_version='1', initial_device_readback_version='1',
            molecule_is_host_metadata='1').items():
        assert fields.get(key) == expected, key + ' differs'
    executable = Path(entry['command'][0])
    manifest = executable.parent/'manifest.json'
    assert fields['executable'] == str(executable)
    assert fields['build_manifest'] == str(manifest)
    embedded = json.loads('\n'.join(line[len('# build '):] for line in lines if line.startswith('# build ')))
    assert embedded == e2.campaign.load_json(manifest)
    assert embedded['executable_sha256'][str(executable)] == e2.campaign.sha256(executable)
    rows = [line.split() for line in lines if line.startswith('particle ')]
    assert len(rows) == len(parent['atoms']) == 43563
    assert '# readback_pass=0' in lines[-1]
    partners = {i: -1 for i in parent['atoms']}
    for a, b in pairs:
        assert partners[a] == partners[b] == -1
        partners[a], partners[b] = b-1, a-1
    signed = [[], [], []]
    expected_wrong = [0, 0, 0]
    expected_original = [0, 0, 0]
    examples = []
    for i, row in enumerate(rows, 1):
        assert len(row) == 20
        assert list(map(int, row[1:5])) == [i-1, i-1, *parent['atoms'][i]]
        assert float(row[5]) == parent['atoms'][i][1]
        assert list(map(int, row[6:8])) == [partners[i], partners[i]]
        values = list(map(float, row[8:]))
        assert all(math.isfinite(x) for x in values)
        expected_xyz, actual_xyz = values[:3], values[3:6]
        assert expected_xyz == actual_xyz == represented_position(parent['positions'][i], parent['bounds'])
        audit = velocity_audit(parent['velocities'][i], values[6:9], values[9:])
        assert all(audit['actual_matches_represented']), 'actual GPU velocity differs from parent float32'
        for axis in range(3):
            signed[axis].append(audit['signed_native_comparison_error'][axis])
            expected_wrong[axis] += not audit['recorded_expected_matches_represented'][axis]
            expected_original[axis] += audit['recorded_expected_matches_serialized'][axis]
        if len(examples) < 3 and not all(audit['recorded_expected_matches_represented']):
            examples.append(dict(particle_id=i, serialized_velocity=parent['velocities'][i],
                recorded_expected_velocity=values[6:9], device_velocity=values[9:]))
    return dict(particles=len(rows),native_readback_status='failed',
        actual_position_velocity_id_type_partner_audit='exact_match_to_authenticated_representation',
        max_position_error=0, expected_velocity_wrong_by_axis=expected_wrong,
        expected_equals_serialized_by_axis=expected_original,
        actual_velocity_correct_by_axis=[len(rows)]*3,
        max_native_velocity_error_by_axis=[max(map(abs, values)) for values in signed],
        recorded_header=fields, embedded_build_authenticated=True,
        examples=examples,sha256=e2.campaign.sha256(path)), signed


def analyze(work=WORK):
    prepared=e2.campaign.load_json(work/'PREPARED.json')
    e2.check_hashes(e2.campaign.load_json(work/'NEW_OUTPUTS_SHA256.json'))
    histories=[]
    parents={}
    readback=None
    errors=None
    for item in prepared:
        attempt=Path(item['attempt'])
        plan=e2.check_plan(ROOT,attempt)
        assert plan['steps']==10000 and plan['smoke'] is True
        assert e2.campaign.sha256(attempt/'plan.json')==item['plan_sha256']
        e2.approval_record(attempt/'approval.json',attempt/'plan.json','e2_derived_smoke')
        for entry in plan['histories']:
            assert (entry['start_step'],entry['end_step'])==(8000000,8010000)
            directory=Path(entry['output_prefix']).parent
            replica=entry['replica']
            if replica not in parents:
                system,initial=e2.validation.read_parent(entry)
                data=e2.campaign.parse_lammps_data(entry['parent']['snapshot'])
                graph=prior.graph_summary(initial['pairs'],system)
                _,states=e2.validation.analysis.stationarity.read_state(entry['parent']['prefix']+'.state')
                shape=e2.validation.snapshot_conformation(entry['parent']['snapshot'],4)
                parents[replica]=dict(parent=entry['parent'],graph=graph,
                    final_reference_state=states[-1],conformation_from_parent_snapshot=dict(
                        mean_rg2=shape[0],mean_center_terminal_r2=shape[1]),
                    inherited_creations=initial['creations'],inherited_breaks=initial['breaks'])
            failed=(directory/'incomplete.json').exists()
            assert not (directory/'complete.json').exists()
            row=dict(system=entry['system']['system_id'],Ea=entry['physics']['Ea'],replica=replica,
                status='failed_before_MD' if failed else 'not_executed',additional_MD_steps=0,
                plan_sha256=item['plan_sha256'],approval_sha256=e2.campaign.sha256(attempt/'approval.json'),
                attempt=str(attempt),parent=entry['parent'],lineage=entry['lineage'],
                chemistry_seed=entry['chemistry_seed'],md_seed=entry['md_seed'],effective_md_seed=entry['effective_md_seed'],
                start_step=8000000,maximum_end_step=8010000,observed_final_step=None,
                q=-math.expm1(-20*math.exp(-entry['physics']['Ea'])),
                event_counts=None,event_integrated_exposures=None,event_rates=None,final_observables=None)
            row['q_relative_control']=row['q']/(-math.expm1(-20*math.exp(-4)))
            if failed:
                assert entry['system']['Ea']==4 and replica==1
                stderr=(directory/'stderr.log').read_text()
                assert 'CUDA initialized' in stderr
                assert 'initial device state differs from authenticated loader representation' in stderr
                assert f"requested_seed={entry['md_seed']} effective_seed={entry['effective_md_seed']} internal_start_step=0" in stderr
                assert not list(directory.glob('state.candidate_mismatch.tsv'))
                for suffix in ('.events','.state','.numerics.tsv','.conformation.tsv'):
                    assert Path(entry['output_prefix']+suffix).stat().st_size==0
                assert Path(entry['output_prefix']+'.candidate_validation.tsv').read_text()==(
                    '# step candidates oracle_verified_active_candidates\n')
                for suffix in ('.restart.lammpsdat','.assoc_restart'):
                    assert not Path(entry['output_prefix']+suffix).exists()
                system,initial=e2.validation.read_parent(entry)
                data=e2.campaign.parse_lammps_data(entry['parent']['snapshot'])
                readback,errors=readback_audit(Path(entry['output_prefix']+'.initial_device_validation.tsv'),data,initial['pairs'],entry)
                row.update(event_counts=dict(creations=0,breaks=0,neighbor_gains=0,neighbor_losses=0),
                    event_integrated_exposures=dict(active_bond_time=0,free_sticker_time=0,physical_duration=0),
                    observed_initial_step=8000000,device_audit=readback,
                    failure_receipt=e2.campaign.load_json(directory/'incomplete.json'))
            else:
                assert not list(directory.iterdir())
            histories.append(row)
    assert len(histories)==12 and sum(h['status']=='failed_before_MD' for h in histories)==1
    assert readback is not None
    return dict(decision='failed_hold_no_kinetic_screen',histories=histories,parents=parents,
        additional_MD_steps=0,authorized_step_cap=120000,started_histories=1,unstarted_histories=11,
        candidate_oracle_sweeps_executed=0,device_readbacks_executed=1,native_readback_passes=0,
        independent_parent_families=3,bitwise_MD_continuation=False),errors


def write_results(report,errors,output):
    output.mkdir(parents=True,exist_ok=True)
    (output/'RESULTS.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    fields=['system','replica','status','additional_MD_steps','chemistry_seed','md_seed','effective_md_seed',
            'q','q_relative_control','plan_sha256','approval_sha256']
    with (output/'HISTORIES.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in report['histories']:
            writer.writerow({k:row[k] for k in fields})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(11,3),constrained_layout=True)
    for axis,values,label in zip(axes,errors,'xyz'):
        axis.hist(values,bins=50)
        axis.set(title=label,xlabel='Device − recorded expected velocity',ylabel='Particles')
    fig.suptitle('Failed pre-MD readback: actual velocities all match parent float32')
    fig.savefig(output/'READBACK_ERRORS.png',dpi=150)
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=WORK)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    write_results(*analyze(args.work),args.output)
