"""Read-only Ea feasibility calculations; writes only to a new review-output directory."""
import argparse
import itertools
import json
import math
from pathlib import Path
import statistics
import sys

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ROOT = REPO / 'examples/KG_Assoc/kg_assoc_100m'
sys.path[:0] = [str(REPO / 'examples/KG_Assoc/campaign'),
                str(REPO / 'examples/KG_Assoc/analysis')]
import kg_assoc_e2 as e2
import kg_assoc_e2_registry as registry
import kg_assoc_c1_recovery as recovery
from catalog_model import Catalog

REFERENCE = 'F04_N010_RP080_EE08_EA04'
RECORD = ROOT / ('banks/e2_acceptance/' + REFERENCE + '_8M_qualified_20261013_v1.json')


def attempt(ea, temperature=1.0, nu0=20.0, every=100, dt=.01):
    return -math.expm1(-nu0 * math.exp(-ea / temperature) * every * dt)


def matching_kernel(q, energies=(-2.0, .7, 1.5), order=(0, 1, 2)):
    """Enumerate an ideal-random fixed-geometry four-sticker path, not MD."""
    edges = ((0, 1), (1, 2), (2, 3))
    states = [frozenset(indices) for n in range(4)
              for indices in itertools.combinations(range(3), n)
              if len({v for i in indices for v in edges[i]}) == 2 * n]
    weights = [math.exp(-sum(energies[i] for i in state)) for state in states]
    target = [w / sum(weights) for w in weights]
    matrix = []
    for start in states:
        distribution = {start: 1.0}
        for edge in order:
            updated = {}
            for state, probability in distribution.items():
                occupied = {v for i in state for v in edges[i]}
                creation = edge not in state
                eligible = not creation or not (occupied & set(edges[edge]))
                p = q * min(1.0, math.exp((-1 if creation else 1) * energies[edge]))
                p = p if eligible else 0.0
                changed = state ^ {edge}
                updated[state] = updated.get(state, 0.0) + probability * (1 - p)
                if p:
                    updated[changed] = updated.get(changed, 0.0) + probability * p
            distribution = updated
        matrix.append([distribution.get(state, 0.0) for state in states])
    return states, target, matrix


def verify_inputs():
    for filename in ('PRESERVED_SHA256.json', 'SOURCE_SHA256.json'):
        e2.check_hashes(e2.campaign.load_json(HERE / filename))
    records = []
    previous = e2.campaign.load_json(REPO /
        'examples/KG_Assoc/reviews/e2_ee12_formal_acceptance_20261016/RECORDS.json')['records']
    expected = {str(REPO / row['record']): row['sha256'] for row in previous}
    e2.require(set(expected) == {str(p) for p in (ROOT / 'banks/e2_acceptance').glob('*.json')},
               'exact twelve prior acceptances required')
    e2.check_hashes(expected)
    for name in sorted(expected):
        record = e2.campaign.load_json(name)
        registry.exclusive_validate(record, [e2.system_by_id(s) for s in record['permitted_systems']])
        records.append(dict(path=name, sha256=expected[name], systems=record['permitted_systems']))
    graph = Catalog(REPO, ROOT).scan()
    e2.require(len(graph['acceptances']) == 12 and not graph['selections'] and
               not graph['registry_views'] and graph['selected_registry'] is None and
               all(s['production_authorization'] == 'absent' for s in graph['systems']),
               'inventory or exclusion state changed')
    return records


def reference_rates():
    archived = e2.campaign.load_json(ROOT / 'aggregate/e2/C1_recovery_review_v1/summary.json')
    record = e2.campaign.load_json(RECORD)
    results = []
    for history in record['histories']:
        replica = history['replica']
        # These calls are CPU readers/replayers; oracle=False avoids executable invocation.
        authenticated = e2.corrected_c1(ROOT, replica, replay=True)
        e2.require(authenticated['prefix'] == history['prefix'], 'wrong reference endpoint')
        parent, _ = recovery.authenticate_parent(ROOT, replica, oracle=False)
        prefix = history['prefix']
        analysis = recovery.analysis
        _, rows = analysis.stationarity.read_state(prefix + '.state')
        system = analysis.topology.read_system(prefix + '.restart.lammpsdat', 2)
        _, raw = analysis.dynamics.read_events(prefix + '.events', system)
        meta, pairs = analysis.restart.read_metadata(str(parent) + '.assoc_restart')
        _, events = analysis.replay(rows, raw, system, network=False, initial=dict(
            pairs=pairs, creations=int(meta['creations']), breaks=int(meta['breaks'])))
        counts = dict(creations=sum(e['type'] == 'C' for e in events),
                      breaks=sum(e['type'] == 'B' for e in events),
                      neighbor_gains=sum(e['neighbor_gain'] for e in events),
                      neighbor_losses=sum(e['neighbor_loss'] for e in events))
        rates = {key: value / 20000 for key, value in counts.items()}
        old = next(r for r in archived['replicas'] if r['replica'] == replica)
        for key, rate in rates.items():
            expected = statistics.mean(w['activity'][key]['mean'] for w in old['corrected'])
            e2.require(math.isclose(rate, expected, abs_tol=1e-12), 'archived event rate differs')
        status = e2.campaign.load_json(Path(prefix).parent / 'status.json')
        results.append(dict(replica=replica, prefix=prefix, start_step=6000000,
            end_step=8000000, chemical_seed=history['chemistry_seed'], counts=counts,
            rates_per_physical_time=rates, wall_seconds=status['wall_seconds'],
            host=status['host'], endpoint_sha256={name: h for name, h in history['sha256'].items()
                if name.endswith(('.restart.lammpsdat', '.assoc_restart'))}))
        print(f'PASS reference r{replica:03d}: numerical/event/network replay and rates', flush=True)
    return results


def calculate(replicas):
    activity = {key: recovery.analysis.dynamics.replica_statistics(
        [r['rates_per_physical_time'][key] for r in replicas])
        for key in replicas[0]['rates_per_physical_time']}
    seconds_per_million = statistics.mean(r['wall_seconds'] for r in replicas) / 2
    scaling = []
    for ea in (4, 6, 8, 10):
        ratio = attempt(ea) / attempt(4)
        rates = {key: value['mean'] * ratio for key, value in activity.items()}
        # Planning scenarios only: neither event matching nor 200 losses certifies equilibrium.
        losses_pilot_million = 200 / rates['neighbor_losses'] / .01 / 1e6
        scaling.append(dict(Ea=ea, q=attempt(ea), q_ratio_to_Ea4=ratio,
            reciprocal_ratio=1 / ratio, arrhenius_rate_ratio=math.exp(-(ea - 4)),
            projected_rates=rates, equivalent_8m_million_steps=8 / ratio,
            equivalent_8m_three_history_gpu_hours=8 / ratio * 3 * seconds_per_million / 3600,
            pilot_200_losses_million_steps=losses_pilot_million,
            pilot_three_history_gpu_hours=losses_pilot_million * 3 * seconds_per_million / 3600))
    matrices = []
    for ea in (4, 6, 8, 10):
        states, target, matrix = matching_kernel(attempt(ea))
        residual = max(abs(sum(target[i] * matrix[i][j] for i in range(len(states))) - target[j])
                       for j in range(len(states)))
        flux = max(abs(target[i] * matrix[i][j] - target[j] * matrix[j][i])
                   for i in range(len(states)) for j in range(len(states)))
        matrices.append(dict(Ea=ea, states=[sorted(s) for s in states], target=target,
                             matrix=matrix, stationary_residual=residual,
                             detailed_balance_residual_for_fixed_order=flux))
    return dict(reference_rates=activity, scaling=scaling, fixed_geometry_example=matrices,
        wall_seconds_per_million_steps=seconds_per_million,
        uncertainty='three original histories, Student-t df=2; projected rates conditional on unchanged opportunity statistics',
        cost_scope='historical host titan, same driver and logging; planning proxy, not a new benchmark',
        conclusion='reference transfer potentially useful; targeted restart and coupled-sampler validation first',
        execution_authorized=False, new_acceptance=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    e2.require(not args.output.exists(), 'new output directory required')
    inventory = verify_inputs()
    replicas = reference_rates()
    summary = calculate(replicas)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in [('REFERENCE.json', replicas), ('CALCULATIONS.json', summary),
                       ('ACCEPTANCES.json', inventory)]:
        e2.exclusive_json(args.output / name, data)
    verify_inputs()
    print('PASS twelve acceptances, all preserved/source bindings, no selection or production authority')


if __name__ == '__main__':
    main()
