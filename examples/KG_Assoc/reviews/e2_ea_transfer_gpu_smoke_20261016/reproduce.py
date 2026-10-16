#!/usr/bin/env python3
"""Read-only capped-smoke replay, event exposures, paired-parent tables and figures."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve()
while not (REPO / 'examples/KG_Assoc/campaign').is_dir():
    REPO = REPO.parent
sys.path.insert(0, str(REPO / 'examples/KG_Assoc/campaign'))
import kg_assoc_e2 as e2

WORK = REPO / 'examples/KG_Assoc/kg_assoc_100m/aggregate/e2/ea_transfer_smoke_20261016_v1'


def exposures(events, initial_bonds, start, end, dt=.01, stickers=4000):
    """Exact event-integrated left-continuous populations; same-step events have zero lag."""
    previous, bonds, integrated = start, initial_bonds, 0.0
    for step, kind, _ in events:
        assert previous <= step <= end and step > start and kind in ('C', 'B')
        integrated += bonds * (step - previous) * dt
        bonds += 1 if kind == 'C' else -1
        assert 0 <= 2 * bonds <= stickers
        previous = step
    integrated += bonds * (end - previous) * dt
    duration = (end - start) * dt
    return dict(active_bond_time=integrated,
                free_sticker_time=stickers * duration - 2 * integrated,
                final_bonds=bonds, physical_duration=duration)


def graph_summary(pairs, system):
    graph = e2.validation.analysis.topology.frame_observables(0, 0, 0,
        [(a, b, system['atom_to_star'][a], system['atom_to_star'][b]) for a, b in pairs], system)
    multiplicities = Counter(graph['edge_multiplicity'].values())
    multiplicities[0] = len(system['stars']) * (len(system['stars']) - 1) // 2 - sum(multiplicities.values())
    return dict(multiplicity={str(i): multiplicities[i] for i in range(5)},
        distinct_degree=dict(sorted(Counter(graph['neighbor_degree'].values()).items())),
        intra_loops=dict(sorted(Counter(graph['intra_degree'][s] for s in system['stars']).items())),
        isolated_stars=sorted(s for s, degree in graph['neighbor_degree'].items() if degree == 0),
        component_sizes=graph['component_sizes'],
        intra=graph['intra_bonds'], inter=graph['inter_bonds'],
        mean_degree=graph['mean_k_neighbor'], giant=graph['largest_component_size'])


def poisson_interval(count, exposure):
    # Conditional counting diagnostic only; correlated network events need not be Poisson.
    from scipy.stats import chi2
    return [float(chi2.ppf(.025, 2 * count) / (2 * exposure)) if count else 0.0,
            float(chi2.ppf(.975, 2 * (count + 1)) / (2 * exposure))]


def analyze(work=WORK):
    histories = []
    outcomes = []
    root = REPO / 'examples/KG_Assoc/kg_assoc_100m'
    fingerprints = {}
    for item in json.loads((work / 'PREPARED.json').read_text()):
        attempt = Path(item['attempt'])
        plan = e2.check_plan(root, attempt)
        assert plan['smoke'] is True and plan['steps'] == 10000
        assert e2.campaign.sha256(attempt / 'plan.json') == item['plan_sha256']
        e2.approval_record(attempt / 'approval.json', attempt / 'plan.json', 'e2_derived_smoke')
        for entry, preflight in zip(plan['histories'], plan['initial_state_checks']):
            directory = Path(entry['output_prefix']).parent
            status = 'validated' if (directory / 'complete.json').exists() else (
                'failed' if (directory / 'incomplete.json').exists() else 'not_executed')
            outcome = dict(system=entry['system']['system_id'], replica=entry['replica'],
                status=status, planned_start=entry['start_step'], planned_end=entry['end_step'],
                chemistry_seed=entry['chemistry_seed'], md_seed=entry['md_seed'],
                effective_md_seed=entry['effective_md_seed'], parent=entry['parent'],
                lineage=entry['lineage'], command=entry['command'], initial_preflight=preflight,
                attempt=str(attempt), source_git_sha=plan['git_sha'],
                executable_sha256=plan['executable_sha256'],
                plan_sha256=e2.campaign.sha256(attempt / 'plan.json'),
                approval_sha256=e2.campaign.sha256(attempt / 'approval.json'),
                files_sha256={str(p): e2.campaign.sha256(p) for p in directory.iterdir() if p.is_file()})
            outcomes.append(outcome)
            if status != 'validated':
                if status == 'failed':
                    prefix = entry['output_prefix']
                    metadata, rows = e2.validation.analysis.stationarity.read_state(prefix + '.state')
                    e2.validation.check_physics(metadata, entry['physics'], state=True)
                    assert int(metadata['seed']) == entry['chemistry_seed']
                    assert int(metadata['md_seed']) == entry['md_seed']
                    assert int(metadata['start_step']) == entry['start_step']
                    system, initial = e2.validation.read_parent(entry)
                    _, raw = e2.validation.analysis.dynamics.read_events(prefix + '.events', system)
                    active, events = e2.validation.analysis.replay(rows, raw, system, initial=initial)
                    values = e2.validation.analysis.numerics(Path(prefix + '.numerics.tsv'), rows, 43563)
                    shapes = [list(map(float,line.split())) for line in
                              Path(prefix + '.conformation.tsv').read_text().splitlines()[1:]]
                    assert len(shapes) == len(rows)
                    parent_temperature = e2.validation.e1.check_snapshot(
                        Path(entry['parent']['snapshot']), entry['system'])['final_temperature']
                    assert math.isclose(values[0][3],parent_temperature,rel_tol=1e-5)
                    for row, numeric, shape in zip(rows, values, shapes):
                        assert shape[0] == row['step'] and all(math.isfinite(x) for x in shape)
                        row.update(temperature=numeric[3], mean_rg2=shape[2],
                                   mean_center_terminal_r2=shape[3])
                    checks = [list(map(int,line.split())) for line in
                              Path(prefix + '.candidate_validation.tsv').read_text().splitlines()[1:]]
                    assert [c[0] for c in checks] == list(range(entry['start_step']+100,
                        checks[-1][0]+1,100))
                    assert all(len(c)==3 and 0 <= c[2] <= c[1] for c in checks)
                    assert all(entry['start_step'] < event[0] <= checks[-1][0] and
                               event[0] % 100 == 0 for event in raw)
                    stderr = (directory / 'stderr.log').read_text()
                    assert (f"requested_seed={entry['md_seed']} "
                            f"effective_seed={entry['effective_md_seed']} internal_start_step=0") in stderr

                    assert 'FAIL: candidate regression: oracle count mismatch' in stderr
                    inferred_stop = checks[-1][0] + entry['physics']['Nevery']
                    outcome.update(error=e2.campaign.load_json(directory / 'incomplete.json'),
                        oracle_failure='candidate regression: oracle count mismatch',
                        last_observed_diagnostic_step=rows[-1]['step'],
                        successful_oracle_sweeps=len(checks), last_successful_oracle_step=checks[-1][0],
                        inferred_failure_step=inferred_stop,
                        inference='next chemistry sweep; checkSweep throws before kinetics.update',
                        counts=dict(creations=sum(e['type']=='C' for e in events),
                            breaks=sum(e['type']=='B' for e in events),
                            neighbor_gains=sum(e['neighbor_gain'] for e in events),
                            neighbor_losses=sum(e['neighbor_loss'] for e in events)),
                        exposure_to_inferred_stop=exposures(raw,len(initial['pairs']),entry['start_step'],inferred_stop),
                        initial=rows[0], last_observed=rows[-1], partial_timeseries=rows,
                        initial_graph=graph_summary(initial['pairs'],system),
                        last_replayed_graph=graph_summary(active,system),
                        no_final_restart_or_chemical_sidecar=True)
                    print('FAILED_PARTIAL_REPLAY_OK',outcome['system'],entry['replica'],flush=True)
                else:
                    assert not list(directory.iterdir())
                continue
            complete = e2.campaign.load_json(directory / 'complete.json')
            assert complete['plan_sha256'] == item['plan_sha256'] and complete['status'] == 'validated'
            e2.check_hashes(complete['output_sha256'])
            rows, events, validation = e2.validation.validate(entry, oracle=True)
            prefix = entry['output_prefix']
            system, initial = e2.validation.read_parent(entry)
            _, raw = e2.validation.analysis.dynamics.read_events(prefix + '.events', system)
            exposure = exposures(raw, len(initial['pairs']), entry['start_step'], entry['end_step'])
            assert exposure['final_bonds'] == rows[-1]['bonds']
            final_meta, final_pairs = e2.validation.analysis.restart.read_metadata(prefix + '.assoc_restart')
            parent_data = e2.campaign.parse_lammps_data(entry['parent']['snapshot'])
            final_data = e2.campaign.parse_lammps_data(prefix + '.restart.lammpsdat')
            assert parent_data['atoms'] == final_data['atoms']
            assert parent_data['bonds'] == final_data['bonds']
            assert parent_data['bounds'] == final_data['bounds']
            fingerprint = tuple(re.search(key + r'=([0-9a-f]+)', preflight).group(1)
                                for key in ('physical_fingerprint', 'chemical_fingerprint'))
            replica = entry['replica']
            assert fingerprints.setdefault(replica, fingerprint) == fingerprint
            counts = dict(creations=sum(e['type'] == 'C' for e in events),
                breaks=sum(e['type'] == 'B' for e in events),
                neighbor_gains=sum(e['neighbor_gain'] for e in events),
                neighbor_losses=sum(e['neighbor_loss'] for e in events))
            checks = [list(map(int, line.split())) for line in
                Path(prefix + '.candidate_validation.tsv').read_text().splitlines()[1:]]
            assert len(checks) == 100
            ea = entry['physics']['Ea']
            q = -math.expm1(-20 * math.exp(-ea))
            all_files = {str(p): e2.campaign.sha256(p) for p in Path(prefix).parent.iterdir() if p.is_file()}
            record = dict(system=entry['system']['system_id'], Ea=ea, replica=replica,
                prefix=prefix, attempt=str(attempt), start_step=entry['start_step'], end_step=entry['end_step'],
                branch_age_start=0, branch_age_end=10000, bitwise_md_continuation=False,
                chemistry_seed=entry['chemistry_seed'], md_seed=entry['md_seed'],
                effective_md_seed=entry['effective_md_seed'], lineage=entry['lineage'],
                parent=entry['parent'], build_manifest=plan['evidence_sha256'],
                executable_sha256=plan['executable_sha256'], source_git_sha=plan['git_sha'],
                initial_preflight=preflight, initial_fingerprints=fingerprint,
                plan_sha256=e2.campaign.sha256(attempt / 'plan.json'),
                approval_sha256=e2.campaign.sha256(attempt / 'approval.json'),
                complete=e2.campaign.load_json(Path(prefix).parent / 'complete.json'),
                output_sha256=all_files, validation=validation, counts=counts, exposure=exposure,
                rates_per_time={k: v / exposure['physical_duration'] for k, v in counts.items()},
                break_rate_per_bond_time=counts['breaks'] / exposure['active_bond_time'],
                break_rate_conditional_poisson95=poisson_interval(counts['breaks'], exposure['active_bond_time']),
                creation_rate_per_free_sticker_time=counts['creations'] / exposure['free_sticker_time'],
                q=q, q_relative_control=q / (-math.expm1(-20 * math.exp(-4))),
                candidate_sweeps=len(checks), candidate_opportunities=sum(c[1] for c in checks),
                eligible_active_opportunities=sum(c[2] for c in checks),
                nonactive_geometric_opportunities=sum(c[1]-c[2] for c in checks),
                initial=dict(rows[0]), final=dict(rows[-1]), timeseries=rows,
                initial_graph=graph_summary(initial['pairs'], system),
                final_graph=graph_summary(final_pairs, system),
                inherited_creations=initial['creations'], inherited_breaks=initial['breaks'],
                final_creations=int(final_meta['creations']), final_breaks=int(final_meta['breaks']))
            histories.append(record)
            print('REPLAY_OK', record['system'], replica, counts, flush=True)
    for row in histories:
        control = next(c for c in histories if c['Ea'] == 4 and c['replica'] == row['replica'])
        row['control_scaled_expected_breaks'] = (control['break_rate_per_bond_time'] *
            row['exposure']['active_bond_time'] * row['q_relative_control'])
        row['paired_initial_identical'] = all(row['initial'][key] == control['initial'][key] for key in
            ('bonds','intra','inter','mean_degree','L1','L2','largest_size',
             'temperature','mean_rg2','mean_center_terminal_r2'))
        assert row['paired_initial_identical']
    assert len(outcomes) == 12
    return dict(histories=histories, outcomes=outcomes,
        validated_additional_steps=len(histories)*10000,
        total_inferred_additional_steps=len(histories)*10000+sum(
            o.get('inferred_failure_step',o['planned_start'])-o['planned_start'] for o in outcomes if o['status']=='failed'),
        authorized_total_step_cap=120000,
        independent_parent_families=3, chemical_streams=12, effective_md_streams=12,
        total_oracle_sweeps=sum(h['candidate_sweeps'] for h in histories))


def write_results(report, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'RESULTS.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    fields = ['Ea','replica','chemistry_seed','md_seed','effective_md_seed','creations','breaks',
              'neighbor_gains','neighbor_losses','active_bond_time','free_sticker_time',
              'q_relative_control','control_scaled_expected_breaks']
    with (output / 'HISTORIES.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in report['histories']:
            flat = row | row['counts'] | row['exposure']
            writer.writerow({key: flat[key] for key in fields})
    fields = ['Ea','replica','phase','bonds','intra','inter','L1','L2','mean_degree',
              'largest_size','mean_rg2','mean_center_terminal_r2','temperature']
    with (output / 'NETWORK_AND_SHAPE.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for h in report['histories']:
            for phase in ('initial','final'):
                values = h[phase] | dict(Ea=h['Ea'],replica=h['replica'],phase=phase)
                writer.writerow({key: values[key] for key in fields})
        for h in report['outcomes']:
            if h['status'] == 'failed':
                for phase in ('initial','last_observed'):
                    values = h[phase] | dict(Ea=8,replica=h['replica'],phase=phase)
                    writer.writerow({key: values[key] for key in fields})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    metrics = ['intra','inter','L1','L2','mean_degree','largest_size','mean_rg2','mean_center_terminal_r2']
    fig, axes = plt.subplots(4, 2, figsize=(10, 12), constrained_layout=True)
    colors = {4:'black',6:'tab:blue',8:'tab:orange',10:'tab:green'}
    series = report['histories'] + [dict(Ea=8,replica=h['replica'],timeseries=h['partial_timeseries'])
        for h in report['outcomes'] if h['status'] == 'failed']
    for ax, key in zip(axes.flat, metrics):
        for h in series:
            age = [(r['step'] - 8000000) * .01 for r in h['timeseries']]
            ax.plot(age,[r[key] for r in h['timeseries']],color=colors[h['Ea']],
                    linestyle=['-', '--', ':'][h['replica']-1], alpha=.8)
        ax.set(title=key, xlabel='Branch physical time (MD steps × .01)')
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([0],[0],color=colors[ea],label=label) for ea,label in
        ((4,'Ea4 control, complete'),(6,'Ea6, complete'),(8,'Ea8 r001, partial'))],
        loc='lower center',bbox_to_anchor=(.5,-.02),ncol=3)
    fig.suptitle('Capped transfer smoke: line style r001/r002/r003; Ea10 not run')
    fig.savefig(output / 'EVOLUTION.png', dpi=150, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=WORK)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    write_results(analyze(args.work),args.output)
