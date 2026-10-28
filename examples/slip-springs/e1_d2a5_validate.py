"""Variable-N campaign completion checks; no scientific acceptance or fitting."""
import csv
import itertools
import math
from pathlib import Path

from e1_d1_pilot import load, require
from e1_d2a3_run import HEADER, PHYSICAL, SPRINGS, exported_grid, matches
from e1_observer_check import verify as verify_context


def finite_json(path):
    value = load(path)
    def visit(item):
        if isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, float):
            require(math.isfinite(item), f'nonfinite JSON: {path}')
    visit(value)
    return value


def curve_header(n):
    selected = [0, n//4, n//2, 3*n//4, n]
    return HEADER[:11] + [f'bead{i}_msd' for i in selected] + HEADER[16:]


def curves(path, run, chains):
    e = run['expected']
    header = curve_header(run['N'])
    support = itertools.product(chains, exported_grid(e))
    count = 0
    with path.open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == header, f'correlation header: {path}')
        for row, item in itertools.zip_longest(reader, support):
            require(row is not None and item is not None, f'correlation row count: {path}')
            chain, (lag, block) = item
            require(set(row) == set(header) and row['chain'] == chain, 'curve identity/order')
            require(all(v is not None and math.isfinite(float(v))
                        for k, v in row.items() if k != 'chain'), 'nonfinite curve')
            expected = dict(replica=run['replica_id'], lag_samples=lag, lag_steps=lag*e['stride'],
                            origins_per_chain=e['dynamics_frames']//block-lag//block,
                            decimation_samples=block, diffusion_phase_samples=block-1,
                            orientation_block_samples=block)
            for key, value in expected.items():
                require(row[key] == str(value), f'curve integer support: {key}')
            require(float(row['lag_time']) == (lag*e['stride'])*e['dt'] and
                    float(row['orientation_block_duration']) == (block*e['stride'])*e['dt'],
                    'curve physical clock')
            count += 1
    return count


def csv_rows(path):
    with path.open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames and len(reader.fieldnames) == len(set(reader.fieldnames)),
                f'missing/duplicate CSV header: {path}')
        headers = {
            'initial.csv':'chain,bead,x,y,z', 'final.csv':'chain,bead,x,y,z',
            'samples.csv':'step,time,chain,mean_r,mean_r2,re2,rg2,cm_msd,monomer_msd,min_length,tangent1,tangent2,tangent3,tangent4',
            'initial_bonds.csv':'chain,bond,length',
            'bond_statistics.csv':'chain,bond,frames,mean_r,mean_r2'+''.join(f',bin{i}' for i in range(33)),
            'fixed_slip_springs.csv':'chain,bead,ax,ay,az',
            'slip_springs_initial.csv':'spring,chain,bead,ax,ay,az',
            'slip_springs_final.csv':'spring,chain,bead,ax,ay,az',
        }
        if path.name in headers:
            require(reader.fieldnames == headers[path.name].split(','), f'CSV schema: {path}')
        for row in reader:
            require(None not in row and all(v is not None and math.isfinite(float(v))
                                           for v in row.values()), f'invalid CSV: {path}')
            yield row


def validate_output(root, run):
    root = Path(root)
    n, z, kappa, seed, e = (run[k] for k in ('N', 'Z', 'kappa', 'seed', 'expected'))
    steps, beads = e['steps'], 256*(n+1)
    physical = PHYSICAL | (SPRINGS if z else set())
    require({p.name for p in root.iterdir()} == physical | {'dynamics'}, 'physical inventory')
    require(all((root/name).is_file() and not (root/name).is_symlink() for name in physical),
            'nonregular physical file')
    documents = {p.name: finite_json(p) for p in root.glob('*.json')}
    complete, main = documents['equilibrium_complete.json'], documents['metadata.json']
    matches(complete, dict(version=1, complete=True, frames=e['full_frames']), 'E1 completion')
    require(set(complete['files']) == physical-{'parameters.txt', 'equilibrium_complete.json'},
            'completion inventory')
    for name, size in complete['files'].items():
        require(type(size) is int and (root/name).stat().st_size == size, 'completion file size')
    matches(main, dict(model='finite-rest-length-Kratky-Porod', precision_bits=64,
                       timer_version=1, springs=n, chains=256, beads_per_chain=n+1,
                       total_beads=beads, dt=.0001, kbt=1, zeta=1, steps=steps,
                       production_time=e['T'], sample=e['scalar_stride'], seed=seed,
                       slip_count=z, slip_ms2=5 if z else None, rng_domain=3,
                       slip_effective_stiffness=.6 if z else None,
                       active_angles=n-1 if kappa else 0, update_launches=steps,
                       stretch_launches=steps+2, bending_launches=steps+2 if kappa else 0,
                       slip_launches=steps+2 if z else 0,
                       slip_mode='canonical-renewal-development' if z else 'disabled',
                       initialization_method='CPU-direct-equilibrium'), 'physical identity')
    require(list(map(float, (root/'parameters.txt').read_text().split())) ==
            [n]+[1,30]*n+[0]+[kappa]*(n-1)+[0], 'backbone parameters')
    matches(documents['equilibrium_schema.json'], dict(
        version=1, phase='initial before dynamics; otherwise after BD and complete jump batch',
        dt=.0001, legacy_sample_stride=e['scalar_stride'], steps=steps, chains=256,
        beads_per_chain=n+1, slip_count=z, canonical=bool(z), expected_frames=e['full_frames'],
        snapshot_steps=[0,steps]), 'E1 schema')
    if z:
        matches(documents['hopping_metadata.json'], dict(version=2, rate=100, interval_bd_steps=1,
                end_renewal=True, batches=steps, poisson_mean=z*100*.0001), 'hopping identity')
    dynamics = root/'dynamics'
    require({p.name for p in dynamics.iterdir()} ==
            {'metadata.json','chain_correlations.csv','replica_correlations.csv'}, 'dynamic inventory')
    m = finite_json(dynamics/'metadata.json')
    matches(m, dict(version=1, complete=True, replica=run['replica_id'], N=n, chains=256,
                    beads_per_chain=n+1, precision_bits=64, seed=seed, dt=.0001, kbt=1, zeta=1,
                    selected_beads=[0,n//4,n//2,3*n//4,n], first_step=0, stride=e['stride'],
                    integration_steps=steps, frames=e['dynamics_frames'], last_step=steps,
                    correlator_levels=e['levels'], correlator_slots=16, correlator_m=2,
                    memory_budget_bytes=512*1024**2, shared_frames=e['scalar_frames'],
                    extra_readbacks=e['dynamics_frames']-e['scalar_frames'],
                    shared_readback_bytes=e['scalar_frames']*beads*32,
                    extra_readback_bytes=(e['dynamics_frames']-e['scalar_frames'])*beads*32,
                    deepest_populated_level_omitted=True, incomplete_blocks_promoted=False,
                    diffusion_point_width_samples=1, independent_replicas=1, standard_error=None,
                    slip_count=z, slip_ms2=5 if z else None, slip_effective_stiffness=.6 if z else 0,
                    hop_rate=100, end_renewal_requested=bool(z), end_renewal_active=bool(z),
                    initialization='CPU-direct-equilibrium', b0=[1]*n, kb=[30]*n,
                    kappa=[0]+[kappa]*(n-1)+[0],
                    initial_phase='initialized state before first BD update, after initial force/state validation',
                    phase='after BD, coordinate-buffer swap and entire hopping/end-renewal batch',
                    coordinates='unwrapped Cartesian; immutable flat chain-contiguous IDs',
                    uncertainty_unit='independent replicas after chain averaging',
                    orientation_lag_half_width='(block_samples-1)*stride*dt',
                    diffusion_semantics='direct displacement; last-position decimation; point width=1; origin stride=b; phase=b-1',
                    orientation_semantics='unit/features formed at fine frames then averaged in blocks b; no block renormalization; triangular lag support'),
            'dynamical identity')
    require(0 < m['conservative_observer_estimate_bytes'] <= m['memory_budget_bytes'], 'observer budget')
    require(m['conservative_observer_estimate_bytes'] == e['observer_estimate_bytes'], 'same-binary allocation estimate')
    for key in ('effective_mobility_step', 'effective_noise'):
        require(m[key] == main[key], 'physical/observer clock/noise')
    counts = {name: curves(dynamics/name, run, chains) for name, chains in (
        ('chain_correlations.csv', map(str,range(256))), ('replica_correlations.csv',['']))}
    expected_rows = {'initial.csv':beads, 'final.csv':beads, 'samples.csv':e['scalar_frames']*256,
                     'initial_bonds.csv':256*n, 'bond_statistics.csv':256*n,
                     'equilibrium_positions.csv':2*beads, 'equilibrium_attachments.csv':2*z,
                     'equilibrium_events.csv':e['full_frames'],
                     'equilibrium_sites.csv':e['full_frames']*beads,
                     'equilibrium_connectors.csv':e['full_frames']*z,
                     'equilibrium_chains.csv':e['full_frames']*256,
                     'equilibrium_tangents.csv':e['full_frames']*256, 'equilibrium_backbone.csv':0}
    if z:
        expected_rows.update({name:z for name in SPRINGS if name.endswith('.csv')})
    for name, expected in expected_rows.items():
        count = 0
        for row in csv_rows(root/name):
            if name == 'samples.csv':
                step = count//256*e['scalar_stride']
                require(row['step'] == str(step) and row['chain'] == str(count%256) and
                        float(row['time']) == step*e['dt'], 'scalar clock/order')
            if name in ('initial.csv', 'final.csv'):
                require(row['chain'] == str(count//(n+1)) and row['bead'] == str(count%(n+1)),
                        'state chain/bead order')
            if name == 'equilibrium_events.csv':
                require(count < len(e['full_steps']) and row['step'] == str(e['full_steps'][count]), 'full E1 schedule')
            count += 1
        require(count == expected, f'physical row count: {name}')
    context = verify_context(root)  # Existing variable-length structural/occupancy checker.
    if z:
        totals = context['totals']
        matches(documents['hopping_metadata.json'], dict(
            batches=totals['batches'], attempts=totals['attempts'], accepted=totals['accepted'],
            outward_proposals=totals['boundary'], occupied_rejected=totals['occupied'],
            metropolis_rejected=totals['metropolis'], renewal_proposed=totals['renewal_proposed'],
            renewal_accepted=totals['renewal_accepted'], renewal_occupied_rejected=totals['renewal_occupied'],
            renewal_same_chain=totals['renewal_same_chain'], renewal_cross_chain=totals['renewal_cross_chain']),
            'final event totals')
    for state, step in (('initial',0), ('final',steps)):
        snapshot = (r for r in csv_rows(root/'equilibrium_positions.csv') if int(r['step']) == step)
        for row, joint in itertools.zip_longest(csv_rows(root/f'{state}.csv'), snapshot):
            require(row is not None and joint is not None and
                    all(row[k] == joint[k] for k in ('chain','bead','x','y','z')), 'joint state agreement')
        if z:
            attached = (r for r in csv_rows(root/'equilibrium_attachments.csv') if int(r['step']) == step)
            for row, joint in itertools.zip_longest(csv_rows(root/f'slip_springs_{state}.csv'), attached):
                require(row is not None and joint is not None and
                        all(row[k] == joint[k] for k in ('spring','chain','bead','ax','ay','az')), 'spring snapshot agreement')
    if z:
        for fixed, mobile in itertools.zip_longest(csv_rows(root/'fixed_slip_springs.csv'),
                                                  csv_rows(root/'slip_springs_initial.csv')):
            require(fixed is not None and mobile is not None and
                    all(fixed[k] == mobile[k] for k in ('chain','bead','ax','ay','az')), 'initial fixed/mobile agreement')
    physical_timers = {k:v for k,v in main.items() if k.endswith('_seconds')}
    dynamic_timers = {k:v for k,v in m.items() if k.endswith('_seconds')}
    require(physical_timers['production_wall_seconds'] > 0 and
            all(v >= 0 for v in [*physical_timers.values(), *dynamic_timers.values()]), 'timers')
    return dict(status='complete_identity_and_acquisition_not_scientific_acceptance',
                curve_rows=counts, context=context, physical_timers=physical_timers,
                dynamics_timers=dynamic_timers, integration_timer_scope=main['integration_timer_scope'],
                dynamics_timer_scope=m['timer_scope'],
                production_steps_per_second=steps/main['production_wall_seconds'],
                observer_estimate_bytes=m['conservative_observer_estimate_bytes'],
                device_array_accounting_bytes=main['device_bytes'], gpu_peak_memory_bytes=None)
