"""Authenticated 24M Ea8/Ea10 continuation plans; no MD in preparation/checks."""
import csv
import hashlib
from pathlib import Path
import re

import kg_assoc_e2 as e2
import kg_assoc_e2_transfer as transfer

MODE = 'Ea_24M_extension_v1'
SCOPE = 'Ea_transfer_24M_extensions_v1'
DURATIONS = {'F04_N010_RP080_EE08_EA08': 16000000,
             'F04_N010_RP080_EE08_EA10': 32000000}
REVIEW = e2.HERE.parent / 'reviews/e2_ea_transfer_24m_joint_20261018'
DOSSIER = e2.HERE.parent / 'reviews/e2_extension_readback_call_cpu_20261019'
BUILD = 'ea_24m_extensions_readback_20261019_v2'
REVIEW_SHA256 = '3d30b0539fa014874acbcad10f5a410053226cf152a872b078fdb031bc4f22d2'
TRANSITIONS_SHA256 = '88c8bbc7fe4ed87124ee71918713ec1eb33345cf4c155876e6f1af28a402692c'
require = e2.require


def endpoint_rows(root, sid):
    require(sid in DURATIONS, 'only the approved Ea8/Ea10 extensions are supported')
    require(e2.campaign.sha256(REVIEW / 'INTEGRITY.sha256') == REVIEW_SHA256,
            'joint scientific review identity differs')
    e2.check_hashes(e2.campaign.load_json(REVIEW / 'INTEGRITY.sha256'))
    with (REVIEW / 'ENDPOINTS.csv').open(newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if int(r['Ea']) == int(sid[-2:])]
    require([int(r['replica']) for r in rows] == [1, 2, 3], 'exact parent triplet absent')
    for row in rows:
        for path_key, hash_key in [('restart', 'restart_sha256'), ('sidecar', 'sidecar_sha256')]:
            path = e2.inside(root, Path(row[path_key]))
            e2.check_hashes({str(path): row[hash_key]})
    return rows


def predecessor(root, sid):
    rows = endpoint_rows(root, sid)
    attempt = Path(rows[0]['restart']).parents[1]
    require(all(Path(r['restart']).parents[1] == attempt for r in rows), 'mixed parent attempts')
    require(e2.campaign.sha256(attempt / 'plan.json') == rows[0]['plan_sha256'],
            '24M source plan differs')
    plan = e2.campaign.load_json(attempt / 'plan.json')
    require(plan['lineage_mode'] == transfer.MODE and plan['system']['system_id'] == sid and
            plan['steps'] == 16000000 and plan['smoke'] is False, 'wrong 24M predecessor')
    for row, history in zip(rows, plan['histories']):
        require(history['replica'] == int(row['replica']) and history['start_step'] == 8000000 and
                history['end_step'] == 24000000 and
                history['output_prefix'] + '.restart.lammpsdat' == row['restart'],
                'wrong original family or parent endpoint')
        complete_path = Path(history['output_prefix']).parent / 'complete.json'
        require(e2.campaign.sha256(complete_path) == row['complete_sha256'], 'parent receipt differs')
        complete = e2.campaign.load_json(complete_path)
        require(complete['status'] == 'validated' and complete['end_step'] == 24000000 and
                complete['plan_sha256'] == row['plan_sha256'] and
                complete['validation']['oracle_sweeps'] == 160000 and
                complete['validation']['initial_device_readback']['status'] == 'valid',
                'parent numerical qualification absent')
        e2.check_hashes(complete['output_sha256'])
        e2.check_hashes(history['parent']['sha256'])
    e2.check_hashes(plan['executable_sha256'])
    e2.check_hashes(plan['build']['build_log_sha256'])
    e2.check_hashes(plan['evidence_sha256'])
    return attempt, plan, rows


def parent_descriptor(attempt, prior):
    directory = Path(prior['output_prefix']).parent
    complete = e2.campaign.load_json(directory / 'complete.json')
    paths = [Path(n) for n in complete['output_sha256']]
    paths += [directory / 'complete.json', attempt / 'plan.json']
    return dict(kind='e2', prefix=prior['output_prefix'],
                snapshot=prior['output_prefix'] + '.restart.lammpsdat', sha256=e2.hash_files(paths))


def validate_lineage(entry, metadata, pairs):
    """No recursive plan validation: exact parent hashes close the ancestry here."""
    parent, lineage = entry['parent'], entry['lineage']
    root = Path(lineage['parent_plan']).parents[4]
    sid = entry['system']['system_id']
    attempt, plan, rows = predecessor(root, sid)
    replica = entry['replica']
    require(type(replica) is int and replica in (1, 2, 3), 'invalid continuation family')
    prior = plan['histories'][replica - 1]
    require(parent == parent_descriptor(attempt, prior), '24M parent descriptor differs')
    reservation_path = Path(lineage['seed_reservations'])
    policy = reservation(root, reservation_path, Path(entry['output_prefix']).parents[1], sid)
    stream = policy['streams'][replica - 1]
    expected = dict(mode=MODE, reference_control=False, system_id=sid,
        target_Ea=entry['system']['Ea'], parent_Ea=entry['system']['Ea'],
        parent_chemistry_seed=prior['chemistry_seed'], branch_origin_step=24000000,
        parent_creations=int(metadata['creations']), parent_breaks=int(metadata['breaks']),
        initial_bonds=len(pairs), parent_plan=str(attempt / 'plan.json'),
        parent_plan_sha256=rows[replica - 1]['plan_sha256'],
        seed_reservations=str(reservation_path),
        seed_reservations_sha256=e2.campaign.sha256(reservation_path),
        original_parent_replica=replica, original_branch_id=prior['lineage']['branch_id'],
        reference_acceptance=prior['lineage']['reference_acceptance'],
        reference_acceptance_sha256=prior['lineage']['reference_acceptance_sha256'],
        chemistry_continuation='same_seed_absolute_step_keys', bitwise_md_continuation=False,
        branch_id=sid + ':' + Path(entry['output_prefix']).parents[1].name + f':r{replica:03d}')
    require(lineage == expected and entry['chemistry_seed'] == int(metadata['seed']) ==
            prior['chemistry_seed'] and entry['md_seed'] == stream['md_seed'] and
            entry['effective_md_seed'] == stream['effective_md_seed'] and
            entry['start_step'] == 24000000 and entry['end_step'] == 24000000 + DURATIONS[sid] and
            entry['parent_Ea'] == entry['physics']['Ea'] == entry['system']['Ea'] and
            entry['physics'] == prior['physics'], 'extension chemistry/lineage/steps differ')


def reservation(root, path, attempt, sid):
    path = Path(path).resolve()
    require(path.parent == root / 'banks/e2_md_reservations', 'wrong MD reservation directory')
    record = e2.campaign.load_json(path)
    require(record['schema_version'] == 1 and record['purpose'] == SCOPE and
            record['attempt'] == str(attempt) and record['system'] == sid and
            [r['replica'] for r in record['streams']] == [1, 2, 3], 'wrong MD reservation identity')
    require(all(type(r['replica']) is int for r in record['streams']), 'invalid MD reservation replica type')
    requested = [r['md_seed'] for r in record['streams']]
    effective = [r['effective_md_seed'] for r in record['streams']]
    require(len(set(requested)) == len(set(effective)) == 3 and
            all(e2.validation.effective_md_seed(s) == v for s, v in zip(requested, effective)),
            'MD reservation collision or incorrect effective stream')
    chemical, used, kernels, _ = transfer.streams_in_use(
        root, ignore_attempt=attempt, ignore_md_reservation=path)
    require(not set(requested) & (chemical | used) and not set(effective) & kernels,
            'MD reservation collides with recorded or policy streams')
    # Reserved streams belong to exactly one immutable plan, including unstarted rows.
    for other in (root / 'banks/e2_md_reservations').glob('*.json'):
        if other.resolve() == path:
            continue
        policy = e2.campaign.load_json(other)
        require(not set(requested) & {r['md_seed'] for r in policy['streams']} and
                not set(effective) & {r['effective_md_seed'] for r in policy['streams']},
                'MD continuation reservations collide')
    for other in [transfer.RESERVATIONS, *(root / 'banks/e2_seed_reservations').glob('*.json')]:
        policy = e2.campaign.load_json(other)
        require(not set(requested) & {r[k] for r in policy['streams'] for k in ('md_seed', 'chemistry_seed')} and
                not set(effective) & {e2.validation.effective_md_seed(r['md_seed']) for r in policy['streams']},
                'MD stream collides with a historical reservation')
    for other in (root / 'banks/e2_attempts').glob('*/*/plan.json'):
        if other.parent == attempt:
            continue
        histories = e2.campaign.load_json(other)['histories']
        require(not set(requested) & {h[k] for h in histories for k in ('md_seed', 'chemistry_seed')} and
                not set(effective) & {h['effective_md_seed'] for h in histories},
                'MD stream collides with another attempt')
    return record


def reserve_md(root, attempt, sid):
    chemical, requested, effective, _ = transfer.streams_in_use(root)
    for path in [transfer.RESERVATIONS, *(root / 'banks/e2_seed_reservations').glob('*.json')]:
        for row in e2.campaign.load_json(path)['streams']:
            chemical.add(row['chemistry_seed'])
            requested.add(row['md_seed'])
            effective.add(e2.validation.effective_md_seed(row['md_seed']))
    seed = max(requested, default=1000000) + 1
    streams = []
    while len(streams) < 3:
        kernel = e2.validation.effective_md_seed(seed)
        if seed not in chemical | requested and kernel not in effective:
            streams.append(dict(replica=len(streams) + 1, md_seed=seed, effective_md_seed=kernel))
            requested.add(seed)
            effective.add(kernel)
        seed += 1
    path = root / 'banks/e2_md_reservations' / (attempt.name + '.json')
    e2.exclusive_json(path, dict(schema_version=1, purpose=SCOPE, system=sid,
        attempt=str(attempt), streams=streams, chemistry_policy='inherited; no chemistry allocation'))
    reservation(root, path, attempt, sid)
    return path


def inspect(root, output, sid, build_directory, reservation_path):
    output = e2.inside(root, output)
    require(sid in DURATIONS and output.parent == root / 'banks/e2_attempts/F04_N010_RP080_EE08' and
            re.fullmatch('extension_' + sid + r'_[A-Za-z0-9_]+', output.name),
            'unsupported extension scope/output identity')
    attempt, previous, rows = predecessor(root, sid)
    policy = reservation(root, reservation_path, output, sid)
    histories = []
    for prior, stream in zip(previous['histories'], policy['streams']):
        replica = prior['replica']
        parent = parent_descriptor(attempt, prior)
        metadata, pairs = e2.validation.analysis.restart.read_metadata(parent['prefix'] + '.assoc_restart')
        lineage = dict(mode=MODE, reference_control=False, system_id=sid,
            target_Ea=prior['physics']['Ea'], parent_Ea=prior['physics']['Ea'],
            parent_chemistry_seed=prior['chemistry_seed'], branch_origin_step=24000000,
            parent_creations=int(metadata['creations']), parent_breaks=int(metadata['breaks']),
            initial_bonds=len(pairs), parent_plan=str(attempt / 'plan.json'),
            parent_plan_sha256=rows[replica - 1]['plan_sha256'],
            seed_reservations=str(reservation_path),
            seed_reservations_sha256=e2.campaign.sha256(reservation_path),
            original_parent_replica=replica, original_branch_id=prior['lineage']['branch_id'],
            reference_acceptance=prior['lineage']['reference_acceptance'],
            reference_acceptance_sha256=prior['lineage']['reference_acceptance_sha256'],
            chemistry_continuation='same_seed_absolute_step_keys', bitwise_md_continuation=False,
            branch_id=sid + ':' + output.name + f':r{replica:03d}')
        entry = dict(replica=replica, system=previous['system'], parent=parent,
            parent_Ea=prior['physics']['Ea'], physics=prior['physics'], chemistry_seed=prior['chemistry_seed'],
            md_seed=stream['md_seed'], effective_md_seed=stream['effective_md_seed'],
            start_step=24000000, end_step=24000000 + DURATIONS[sid], lineage=lineage,
            executable_directory=str(build_directory), output_prefix=str(output / f'r{replica:03d}/state'))
        entry['command'] = e2.command(entry, False)
        e2.validation.read_parent(entry)
        histories.append(entry)
    return dict(schema_version=1, stage='E2-G1', lineage_mode=MODE, dataset_root=str(root),
        attempt=str(output), system=previous['system'], histories=histories, steps=DURATIONS[sid],
        smoke=False, preparation_Ea=previous['preparation_Ea'], reference_control=False,
        parent_attempt=str(attempt), segment_index=previous['segment_index'] + 1,
        reservation_id=Path(reservation_path).stem,
        reservation_sha256=e2.hash_files([reservation_path]), diagnostic_window_steps=500000,
        rng_policy='inherited_chemistry_absolute_step_keys; fresh_GJ_MD; no_cross_segment_IAT_or_lifetimes',
        scientific_status='hold_pending_extension_review', production_authorization=False)


def prepare(root, output, sid, build_directory, evidence):
    e2.clean_tree()
    build, manifest = e2.check_build(build_directory)
    e2.require_extension_readback_build(build)
    require(build['out_of_tree'] and not output.exists(), 'new out-of-tree extension attempt required')
    with (root / 'banks/.e2.prepare.lock').open('x'):
        pass
    try:
        policy_path = reserve_md(root, output, sid)
        plan = inspect(root, output, sid, build_directory, policy_path)
        checks = []
        for entry in plan['histories']:
            checked = e2.subprocess.run(entry['command'] + ['--validate-initial-state'],
                check=True, capture_output=True, text=True, timeout=60)
            require('INITIAL_STATE_VALIDATED' in checked.stdout, 'host parent initialization failed')
            actual = e2.subprocess.check_output([str(build_directory / 'kg_assoc_stars'),
                '--md-seed-info', str(entry['md_seed'])], text=True, timeout=60)
            require(int(actual) == entry['effective_md_seed'], 'native MD stream identity differs')
            checks.append(checked.stdout.strip())
        plan.update(git_sha=e2.campaign.git_sha(), source_sha256=e2.sources(), build=build,
            executable_sha256=e2.hash_files([build_directory / n for n in e2.EXECUTABLES]),
            initial_state_checks=checks, evidence_sha256=e2.hash_files([evidence, manifest]))
        require(code_compatible(e2.campaign.load_json(Path(plan['parent_attempt']) / 'plan.json'), plan),
                'extension changes exceed the authenticated validation/front-end transition')
        output.mkdir(parents=True, exist_ok=False)
        e2.exclusive_json(output / 'plan.json', plan)
        for replica in (1, 2, 3):
            (output / f'r{replica:03d}').mkdir()
        return plan
    finally:
        (root / 'banks/.e2.prepare.lock').unlink()


def check_plan(root, output, plan, live=False):
    require(len(plan['reservation_sha256']) == 1, 'one MD reservation required')
    e2.check_hashes(plan['reservation_sha256'])
    directory = Path(next(n for n in plan['executable_sha256'] if Path(n).name == 'kg_assoc_stars')).parent
    expected = inspect(root, output, plan['system']['system_id'], directory,
                       Path(next(iter(plan['reservation_sha256']))))
    require(all(plan.get(k) == value for k, value in expected.items()), 'extension plan identity differs')
    require(len(plan['initial_state_checks']) == 3 and
            all('INITIAL_STATE_VALIDATED' in s for s in plan['initial_state_checks']),
            'host initialization receipts absent')
    e2.check_hashes(plan['evidence_sha256'])
    require(directory == root / 'builds' / BUILD and
            plan['build']['source_sha256'] == plan['source_sha256'] and
            plan['build'] == e2.campaign.load_json(directory / 'manifest.json') and
            plan['executable_sha256'] == e2.hash_files([directory / n for n in e2.EXECUTABLES]),
            'build manifest or executable set differs')
    require(code_compatible(e2.campaign.load_json(Path(plan['parent_attempt']) / 'plan.json'), plan),
            'extension source exceeds approved front-end changes')
    if live:
        e2.require_extension_readback_build(plan['build'])
        e2.live_code(plan)
    return plan


def code_compatible(parent, plan):
    """Only the exact reviewed front-end transition may inherit historical GPU evidence."""
    transition_path = DOSSIER / 'VALIDATION_TRANSITIONS.log'
    if e2.campaign.sha256(transition_path) != TRANSITIONS_SHA256:
        return False
    transitions = e2.campaign.load_json(transition_path)
    before = e2.scientific_source_hashes(parent['source_sha256'])
    after = e2.scientific_source_hashes(plan['source_sha256'])
    for name in ('kg_assoc_e2_extension.py', 'run_ea_extensions.py'):
        after.pop(str(e2.HERE / name), None)
    header = str(e2.HERE.parent / 'kg_assoc_readback_dispatch.cuh')
    if after.pop(header, None) != '27b78580c23a285c5a1375ad953583ea6f841c75104f2bb6af69c35b1d582812':
        return False
    if set(before) != set(after):
        return False
    for relative, record in transitions.items():
        path = e2.HERE.parent / relative
        name = str(path)
        text = path.read_text()
        if before.get(name) != record['before_sha256'] or after.get(name) != record['after_sha256'] or \
                hashlib.sha256(text.encode()).hexdigest() != record['after_sha256']:
            return False
        for change in reversed(record['changes']):
            lines = text.splitlines(keepends=True)
            begin, end = change['after_start'], change['after_end']
            if ''.join(lines[begin:end]) != change['after']:
                return False
            lines[begin:end] = [change['before']]
            text = ''.join(lines)
        if hashlib.sha256(text.encode()).hexdigest() != before[name]:
            return False
        after[name] = before[name]
    if before != after:
        return False
    e2.check_hashes(parent['executable_sha256'])
    e2.check_hashes(plan['executable_sha256'])
    return True


def inherited_gpu_evidence(root, plan):
    attempt, previous, _ = predecessor(root, plan['system']['system_id'])
    require(code_compatible(previous, plan), 'parent GPU evidence is not source-compatible')
    # The immediate same-Ea 24M endpoint is checked again before each selected GPU launch.
    return e2.hash_files([attempt / 'plan.json'] +
        [attempt / f'r{r:03d}/complete.json' for r in (1, 2, 3)])


def revalidate_parent(entry):
    root = Path(entry['lineage']['parent_plan']).parents[4]
    _, previous, _ = predecessor(root, entry['system']['system_id'])
    prior = previous['histories'][entry['replica'] - 1]
    _, _, validation = e2.validation.validate(prior, oracle=True)
    complete = e2.campaign.load_json(Path(prior['output_prefix']).parent / 'complete.json')
    require(validation == complete['validation'], 'independent 24M parent replay differs')


def atomic_receipt(path, record):
    """Publish a complete JSON receipt atomically, never replacing an existing file."""
    import os
    import uuid
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    e2.exclusive_json(temporary, record)
    os.link(temporary, path)
    temporary.unlink()


def parent_death_guard(parent_pid):
    """Linux child supervision only; does not alter simulation state or random streams."""
    def install():
        import ctypes
        import os
        import signal
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(1, signal.SIGTERM, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), 'cannot install parent-death signal')
        if os.getppid() != parent_pid:
            os.kill(os.getpid(), signal.SIGTERM)
    return install


def process_identity(pid):
    require(type(pid) is int and pid > 0, 'invalid native PID receipt')
    stat = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                start_ticks=stat[19])


def native_running(path, plan_sha256, command):
    if not path.exists():
        return False
    record = e2.campaign.load_json(path)
    require(record['plan_sha256'] == plan_sha256 and record['command'] == command,
            'native process receipt identity differs')
    try:
        identity = process_identity(record['pid'])
        state = Path(f"/proc/{record['pid']}/stat").read_text().rsplit(')', 1)[1].split()[0]
    except FileNotFoundError:
        return False
    return all(record[key] == value for key, value in identity.items()) and state != 'Z'


def launch_scope(plan, replica, replicas):
    sid = plan['system']['system_id']
    require(sid in DURATIONS and plan.get('smoke') is False and
            plan.get('reference_control') is False and type(plan['steps']) is int and
            plan['steps'] == DURATIONS[sid] and
            [h['replica'] for h in plan['histories']] == [1, 2, 3] and
            all(type(h['replica']) is int and h['start_step'] == 24000000 and
                h['end_step'] == 24000000 + DURATIONS[sid] for h in plan['histories']),
            'extension scope must be the exact authorized 24M-parent triplet')
    require(replica is None and type(replicas) is list and bool(replicas) and
            all(type(r) is int for r in replicas) and replicas == sorted(set(replicas)) and
            set(replicas) <= {1, 2, 3}, 'extension requires explicit approved replica selection')
    return [h for h in plan['histories'] if h['replica'] in replicas]


def check_approval(record, plan, replica, replicas):
    selected = launch_scope(plan, replica, replicas)
    require(record.get('purpose') == 'e2_derived_extension' and
            record.get('selector_scope') == SCOPE and
            record.get('authorized_system') == plan['system']['system_id'] and
            type(record.get('authorized_replicas')) is list and
            all(type(r) is int for r in record['authorized_replicas']) and
            record['authorized_replicas'] == replicas and
            all(type(record.get(key)) is int and record[key] == value for key, value in (
                ('maximum_additional_MD_steps_per_history', plan['steps']),
                ('maximum_additional_MD_steps', plan['steps'] * len(selected)),
                ('absolute_start_step', 24000000),
                ('absolute_end_step', 24000000 + plan['steps']),
                ('diagnostic_window_steps', 500000))), 'extension approval identity/cap differs')


def partial_step_bounds(prefix, steps):
    """Only flushed complete records give a lower bound; no checkpoint means no exact count."""
    lower = 0
    for suffix, columns in [('.state', 21), ('.candidate_validation.tsv', 3), ('.numerics.tsv', 6)]:
        path = Path(str(prefix) + suffix)
        if not path.exists():
            continue
        with path.open('rb') as stream:
            stream.seek(max(0, path.stat().st_size - 65536))
            raw = stream.read()
            tail = raw.splitlines()
            if not raw.endswith(b'\n'):
                tail = tail[:-1]
        # The first tail record can be truncated at the seek boundary.
        for line in tail[1:]:
            fields = line.split()
            if not fields or line.startswith(b'#') or len(fields) != columns:
                continue
            try:
                absolute = int(fields[0])
            except ValueError:
                continue
            require(24000000 <= absolute <= 24000000 + steps, 'partial absolute step outside cap')
            lower = max(lower, absolute - 24000000)
    return dict(completed_MD_steps_lower_bound=lower, authorized_MD_steps_upper_bound=steps,
                exact_partial_MD_steps_known=False)
