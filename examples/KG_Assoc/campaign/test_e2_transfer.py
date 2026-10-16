"""CPU-only transfer regression: real immutable parents, host preflight, synthetic fixtures."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import kg_assoc_e2 as e2
import kg_assoc_e2_transfer as transfer
import kg_assoc_e2_registry as registry

ROOT = e2.campaign.REPOSITORY_ROOT / 'examples/KG_Assoc/kg_assoc_100m'
NATIVE = Path(os.environ.get('KG_ASSOC_TRANSFER_HOST_EXE',
                             '/tmp/ea_transfer_cpu_build/kg_assoc_stars'))


def output(root, sid, suffix='fixture'):
    return root / 'banks/e2_attempts/F04_N010_RP080_EE08' / ('derived_' + sid + '_' + suffix)


def synthetic_segment(entry, directory):
    """Static bookkeeping fixture, not MD, equilibration or scientific evidence."""
    entry = copy.deepcopy(entry)
    directory.mkdir(parents=True, exist_ok=True)
    prefix = directory / f"r{entry['replica']:03d}/state"
    prefix.parent.mkdir(exist_ok=True)
    entry['output_prefix'] = str(prefix)
    entry['lineage']['branch_id'] = (entry['system']['system_id'] + ':' + directory.name +
                                    f":r{entry['replica']:03d}")
    entry['end_step'] = entry['start_step'] + 3000
    parent = entry['parent']['prefix']
    _, source = e2.validation.analysis.stationarity.read_state(parent + '.state')
    meta, pairs = e2.validation.analysis.restart.read_metadata(parent + '.assoc_restart')
    physics = dict(entry['physics'])
    physics['T'] = physics.pop('temperature')
    lineage = entry['lineage']
    fields = dict(physics, seed=entry['chemistry_seed'], md_seed=entry['md_seed'],
        input_file=entry['parent']['snapshot'], diagnostic_every=1000,
        total_requested_steps=entry['end_step'], start_step=entry['start_step'],
        total_particles=43563, stickers=4000, permanent_bonds=40000,
        ea_switch=int(entry['physics']['Ea'] != 4), parent_Ea=4, chemistry_sweeps=30,
        candidate_sticker_pairs=0, lineage_mode=transfer.MODE,
        parent_chemistry_seed=lineage['parent_chemistry_seed'], reference_control=0,
        branch_origin_step=8000000, parent_creations=int(meta['creations']),
        parent_breaks=int(meta['breaks']), branch_age_start=0, bitwise_md_continuation=0,
        branch_id=lineage['branch_id'])
    fields['original_lammps_atom_ids'] = '1_based'
    header = '# ' + ' '.join(f'{k}={v}' for k, v in fields.items()) + '\n'
    columns = e2.validation.analysis.stationarity.COLUMNS
    body = next(line for line in reversed(Path(parent + '.state').read_text().splitlines())
                if line.strip() and not line.startswith('#')).split()
    rows = []
    for index in range(4):
        values = body[:]
        step = entry['start_step'] + index * 1000
        values[0:2] = [str(step), str(step * .01)]
        values[16:21] = [str(index * len(pairs)), '1.3' if index else '0', '0', '0', '0']
        rows.append(' '.join(values))
    Path(str(prefix) + '.state').write_text(header + '# ' + columns + '\n' + '\n'.join(rows) + '\n')
    Path(str(prefix) + '.events').write_text(header)
    initial = Path(parent + '.restart.lammpsdat').read_text().split('\n', 1)[1]
    for suffix in ('.restart.lammpsdat', '.final_permanent.lammpsdat'):
        Path(str(prefix) + suffix).write_text(f'Synthetic fixture step {entry["end_step"]}\n' + initial)
    sidecar = Path(parent + '.assoc_restart').read_text()
    for key, value in [('Ea', entry['physics']['Ea']), ('seed', entry['chemistry_seed']),
                       ('completed_steps', entry['end_step'])]:
        sidecar = '\n'.join((f'{key} {value}' if line.startswith(key + ' ') else line)
                            for line in sidecar.splitlines()) + '\n'
    Path(str(prefix) + '.assoc_restart').write_text(sidecar)
    data = e2.campaign.parse_lammps_data(entry['parent']['snapshot'])
    Path(str(prefix) + '.final_associations').write_text(''.join(
        f'{a} {b} {data["atoms"][a][0]} {data["atoms"][b][0]}\n' for a, b in pairs))
    numeric = Path(parent + '.numerics.tsv').read_text().splitlines()[-1].split()[2:]
    shape = e2.validation.snapshot_conformation(entry['parent']['snapshot'], 4)
    Path(str(prefix) + '.numerics.tsv').write_text(
        '# step time kinetic_energy temperature min_permanent_bond max_permanent_bond\n' +
        ''.join(f'{step} {step*.01} ' + ' '.join(numeric) + '\n'
                for step in range(8000000, 8003001, 1000)))
    Path(str(prefix) + '.conformation.tsv').write_text(
        '# step time mean_rg2 mean_center_terminal_r2\n' + ''.join(
            f'{step} {step*.01} {shape[0]} {shape[1]}\n'
            for step in range(8000000, 8003001, 1000)))
    (prefix.parent / 'stderr.log').write_text(
        f"[E2 MD stream] requested_seed={entry['md_seed']} "
        f"effective_seed={entry['effective_md_seed']} internal_start_step=0\n" +
        ''.join(f'[VerletNVT::GronbechJensen] {k}: {v}\n' for k, v in
                [('Temperature', '1.000000'), ('Time step', '0.010000'), ('Friction', '0.500000')]))
    return entry


class TransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record, cls.parents = transfer.reference(ROOT)
        cls.plans = {sid: transfer.inspect(ROOT, output(ROOT, sid), sid,
                     control=sid == transfer.REFERENCE) for sid in (*transfer.TARGETS, transfer.REFERENCE)}

    def test_all_twelve_streams_and_exact_inherited_states(self):
        chemical, md = set(), set()
        for sid, plan in self.plans.items():
            self.assertFalse(Path(plan['attempt']).exists())
            self.assertEqual(plan['system']['system_id'], sid)
            for entry in plan['histories']:
                _, state = e2.validation.read_parent(entry)
                meta, pairs = e2.validation.analysis.restart.read_metadata(entry['parent']['prefix'] + '.assoc_restart')
                self.assertEqual(state['pairs'], pairs)
                self.assertEqual(state['creations'], int(meta['creations']))
                self.assertEqual(state['breaks'], int(meta['breaks']))
                self.assertEqual(entry['start_step'], 8000000)
                self.assertEqual(entry['lineage']['branch_origin_step'], 8000000)
                chemical.add(entry['chemistry_seed'])
                md.add(entry['effective_md_seed'])
                actual = subprocess.check_output([str(NATIVE), '--md-seed-info',
                                                  str(entry['md_seed'])], text=True)
                self.assertEqual(int(actual), entry['effective_md_seed'])
        self.assertEqual(len(chemical), 12)
        self.assertEqual(len(md), 12)

    def test_native_initial_state_fidelity_all_targets_and_controls(self):
        self.assertTrue(NATIVE.is_file(), 'compile the affected front end and set KG_ASSOC_TRANSFER_HOST_EXE')
        for replica in (1, 2, 3):
            fingerprints = set()
            for plan in self.plans.values():
                entry = plan['histories'][replica - 1]
                with tempfile.TemporaryDirectory() as temp:
                    command = list(entry['command'])
                    command[0] = str(NATIVE)
                    command[command.index('--output') + 1] = str(Path(temp) / 'never')
                    result = subprocess.run(command + ['--validate-initial-state'], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    fields = dict(token.split('=', 1) for token in result.stdout.split() if '=' in token)
                    fingerprints.add((fields['physical_fingerprint'], fields['chemical_fingerprint']))
                    self.assertEqual(int(fields['seed']), entry['chemistry_seed'])
                    self.assertEqual(int(fields['parent_seed']), entry['lineage']['parent_chemistry_seed'])
                    self.assertEqual(int(fields['creations']), entry['lineage']['parent_creations'])
                    self.assertEqual(int(fields['breaks']), entry['lineage']['parent_breaks'])
                    self.assertEqual(list(Path(temp).iterdir()), [])
            self.assertEqual(len(fingerprints), 1)
            with tempfile.TemporaryDirectory() as temp:
                parent = self.parents[replica - 1]['prefix']
                result = subprocess.run([str(NATIVE), '--restart-prefix', parent,
                    '--output', str(Path(temp) / 'never'), '--validate-initial-state'],
                    capture_output=True, text=True, check=True)
                fields = dict(token.split('=', 1) for token in result.stdout.split() if '=' in token)
                self.assertIn((fields['physical_fingerprint'], fields['chemical_fingerprint']), fingerprints)

    def test_native_rejects_wrong_physics_seeds_and_flags_before_gpu(self):
        entry = self.plans[transfer.TARGETS[0]]['histories'][0]
        with tempfile.TemporaryDirectory() as temp:
            base = [str(NATIVE), '--restart-prefix', entry['parent']['prefix'],
                    '--Ea', '6', '--switch-ea-from', '4', '--reseed-chemistry-from', '22001',
                    '--seed', '620601', '--md-seed', '630601',
                    '--derived-branch-id', entry['lineage']['branch_id'], '--output', str(Path(temp) / 'never'),
                    '--validate-initial-state']
            for key, value in [('--Ea', '5'), ('--switch-ea-from', '6'),
                               ('--reseed-chemistry-from', '22002'), ('--seed', '22001'),
                               ('--seed', '-1'), ('--seed', '123x'), ('--md-seed', '620601')]:
                bad = base[:]
                bad[bad.index(key) + 1] = value
                with self.subTest(key=key, value=value):
                    self.assertNotEqual(subprocess.run(bad, capture_output=True).returncode, 0)
            for flags in [('--dt', '.02'), ('--Ee', '10'), ('--Nevery', '50'),
                          ('--temperature', '2'), ('--r-assoc', '1.2'), ('--K', '31'),
                          ('--nu0', '21'), ('--damp', '3'), ('--arms', '3'),
                          ('--R0', '1.6'), ('--force',), ('--reference-control',)]:
                with self.subTest(flags=flags):
                    self.assertNotEqual(subprocess.run(base + list(flags), capture_output=True).returncode, 0)
            for flag in ('--switch-ea-from', '--reseed-chemistry-from'):
                bad = base[:]
                index = bad.index(flag)
                del bad[index:index + 2]
                self.assertNotEqual(subprocess.run(bad, capture_output=True).returncode, 0)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_native_ordinary_restart_compatibility_and_nonoverwrite(self):
        entry = self.plans[transfer.TARGETS[0]]['histories'][0]
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / 'never'
            base = [str(NATIVE), '--restart-prefix', entry['parent']['prefix'], '--seed', '22001',
                    '--md-seed', '99991', '--output', str(prefix), '--validate-initial-state']
            self.assertEqual(subprocess.run(base, capture_output=True).returncode, 0)
            Path(str(prefix) + '.events').write_text('preserve me')
            self.assertNotEqual(subprocess.run(base, capture_output=True).returncode, 0)
            self.assertEqual(Path(str(prefix) + '.events').read_text(), 'preserve me')

    def test_rejects_substituted_lineage_pairs_physics_and_seeds(self):
        entry = self.plans[transfer.TARGETS[0]]['histories'][0]
        mutations = [('lineage', 'parent_chemistry_seed', 22002), ('lineage', 'parent_creations', 0),
                     ('lineage', 'branch_origin_step', 0), ('lineage', 'reference_control', True),
                     ('physics', 'Ee', 10), ('physics', 'dt', .02), ('parent', 'prefix',
                      str(ROOT / 'banks/e2/F04_N010_RP080_EE08/r001/state'))]
        for category, key, value in mutations:
            bad = copy.deepcopy(entry)
            bad[category][key] = value
            with self.subTest(key=key), self.assertRaises((ValueError, KeyError, FileNotFoundError)):
                e2.validation.read_parent(bad)
        for key, value in [('chemistry_seed', 22001), ('md_seed', 1), ('effective_md_seed', 1)]:
            bad = copy.deepcopy(entry)
            bad[key] = value
            with self.assertRaises(ValueError):
                e2.validation.read_parent(bad)

    def test_reference_hash_corruption_rejected(self):
        with patch.object(transfer, 'ACCEPTANCE_SHA256', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'acceptance identity'):
                transfer.reference(ROOT)

    def test_native_corrupt_sidecar_reciprocity_and_counters_rejected(self):
        entry = self.plans[transfer.TARGETS[0]]['histories'][0]
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / 'parent'
            shutil.copyfile(entry['parent']['snapshot'], str(prefix) + '.restart.lammpsdat')
            original = Path(entry['parent']['prefix'] + '.assoc_restart').read_text()
            lines = original.splitlines()
            index = next(i for i, line in enumerate(lines) if line.startswith('active_bonds '))
            bad_pairs = lines[:]
            bad_pairs[index + 2] = bad_pairs[index + 1]
            bad_counter = original.replace('creations ' + str(entry['lineage']['parent_creations']),
                                           'creations 0')
            for text in ('\n'.join(bad_pairs) + '\n', bad_counter, original.replace('end\n', '')):
                Path(str(prefix) + '.assoc_restart').write_text(text)
                command = entry['command'][:]
                command[0] = str(NATIVE)
                command[command.index('--restart-prefix') + 1] = str(prefix)
                command[command.index('--output') + 1] = str(Path(temp) / 'never')
                self.assertNotEqual(subprocess.run(command + ['--validate-initial-state'],
                                                   capture_output=True).returncode, 0)

    def test_prepare_check_tamper_duplicate_and_approval_gates(self):
        sid = transfer.TARGETS[0]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copyfile(ROOT / 'campaign_protocol.json', root / 'campaign_protocol.json')
            shutil.copyfile(ROOT / 'manifest.json', root / 'manifest.json')
            build = root / 'build'
            build.mkdir()
            for name in e2.EXECUTABLES:
                shutil.copy2(NATIVE, build / name)
            manifest = build / 'manifest.json'
            manifest.write_text('{}')
            build_record = dict(out_of_tree=True, executable_sha256=e2.hash_files(
                [build / name for name in e2.EXECUTABLES]))
            manifest.write_text(json.dumps(build_record))
            evidence = root / 'review.md'
            evidence.write_text('CPU synthetic plan fixture, no execution approval')
            destination = output(root, sid)
            with patch.object(e2, 'clean_tree'), patch.object(e2, 'check_build',
                    return_value=(build_record, manifest)), patch.object(e2, 'sources', return_value={}), \
                    patch.object(transfer, 'reference', return_value=(self.record, self.parents)):
                plan = transfer.prepare(root, destination, sid, 10000, evidence)
                self.assertEqual(e2.check_plan(root, destination), plan)
                self.assertFalse(e2.campaign.load_json(destination / 'approval.example.json')['approved'])
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    transfer.prepare(root, destination, sid, 10000, evidence)
                before = (destination / 'plan.json').read_bytes()
                for key, value in [('chemistry_seed', 22001), ('effective_md_seed', 0),
                                   ('executable_directory', str(root / 'wrong'))]:
                    bad = copy.deepcopy(plan)
                    bad['histories'][0][key] = value
                    (destination / 'plan.json').write_text(json.dumps(bad))
                    with self.assertRaises(ValueError):
                        e2.check_plan(root, destination)
                    (destination / 'plan.json').write_bytes(before)
                # No old-purpose or unsigned approval may reach subprocess/GPU execution.
                with patch.object(e2, 'live_code'):
                    with self.assertRaisesRegex(ValueError, 'invalid approval'):
                        e2.launch(root, destination, execute=True,
                                  approval=destination / 'approval.example.json')
                self.assertTrue(all(not list((destination / f'r{i:03d}').iterdir()) for i in (1, 2, 3)))
                reservation, rows = transfer.reserved_streams(root)
                self.assertEqual(sum(row['claimed'] for row in rows), 3)
                collision = root / 'banks/other.json'
                collision.write_text(json.dumps(dict(histories=[dict(chemistry_seed=620601,
                                                                     prefix='/unrelated')])))
                with self.assertRaisesRegex(ValueError, 'conflicting owners'):
                    transfer.reserved_streams(root)

    def test_unsupported_targets_paths_durations_and_reuse(self):
        for sid, control in [(transfer.REFERENCE, False), (transfer.TARGETS[0], True),
                              ('F04_N010_RP080_EE10_EA04', False)]:
            with self.assertRaises(ValueError):
                transfer.inspect(ROOT, output(ROOT, sid), sid, control=control)
        for steps in (0, 2999, 10001):
            with self.assertRaises(ValueError):
                transfer.inspect(ROOT, output(ROOT, transfer.TARGETS[0]), transfer.TARGETS[0], steps)
        with self.assertRaises(ValueError):
            transfer.inspect(ROOT, ROOT / 'banks/e2_attempts/F04_N010_RP080_EE08/wrong', transfer.TARGETS[0])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            destination = output(root, transfer.TARGETS[0])
            destination.mkdir(parents=True)
            shutil.copyfile(ROOT / 'campaign_protocol.json', root / 'campaign_protocol.json')
            shutil.copyfile(ROOT / 'manifest.json', root / 'manifest.json')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                transfer.inspect(root, destination, transfer.TARGETS[0])

    def test_seed_collisions_in_plans_and_effective_reservations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'banks/e2_attempts/other/attempt/plan.json'
            path.parent.mkdir(parents=True)
            for history in [dict(chemistry_seed=620601), dict(md_seed=630601),
                            dict(effective_md_seed=e2.validation.effective_md_seed(630601))]:
                path.write_text(json.dumps(dict(histories=[history])))
                with self.assertRaisesRegex(ValueError, 'collides'):
                    transfer.reserved_streams(root)

    def test_versioned_reservations_leave_prior_stream_bindings_immutable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'banks/e2_seed_reservations/validation_v2.json'
            path.parent.mkdir(parents=True)
            policy = e2.campaign.load_json(transfer.RESERVATIONS)
            policy['reservation_id'] = 'CPU_fixture_new_independent_stream_set'
            for row in policy['streams']:
                row['chemistry_seed'] += 100000
                row['md_seed'] += 100000
            path.write_text(json.dumps(policy))
            _, rows = transfer.reserved_streams(root, seed_reservations=path)
            self.assertEqual(len(rows), 12)
            self.assertFalse(any(row['claimed'] for row in rows))
            allocated = e2.allocate_md_seeds(root)
            self.assertFalse({e2.validation.effective_md_seed(s) for s in allocated} &
                             {row['effective_md_seed'] for row in rows})
            policy['streams'][0]['chemistry_seed'] = 620401
            path.write_text(json.dumps(policy))
            with self.assertRaisesRegex(ValueError, 'reservation sets collide'):
                transfer.reserved_streams(root, seed_reservations=path)
        bad = copy.deepcopy(self.plans[transfer.TARGETS[0]]['histories'][0])
        bad['lineage']['seed_reservations_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'reservation binding differs'):
            e2.validation.read_parent(bad)

    def test_complete_validator_accepts_synthetic_branch_and_rejects_offsets(self):
        with tempfile.TemporaryDirectory() as temp:
            entry = synthetic_segment(self.plans[transfer.TARGETS[0]]['histories'][0],
                                      Path(temp) / 'synthetic_static_fixture')
            _, _, result = e2.validation.validate(entry)
            self.assertEqual(result['numerical_status'], 'valid')
            self.assertEqual(result['accepted_events'], 0)
            path = Path(entry['output_prefix'] + '.state')
            text = path.read_text()
            path.write_text(text.replace('parent_creations=', 'wrong_parent_creations='))
            with self.assertRaisesRegex(ValueError, 'derived metadata mismatch'):
                e2.validation.validate(entry)

    def test_acceptance_reader_binds_derived_lineage_without_registering(self):
        """An in-memory schema fixture only; no acceptance file or physical trajectory."""
        sid = transfer.TARGETS[0]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('campaign_protocol.json', 'manifest.json'):
                shutil.copyfile(ROOT / name, root / name)
            build = root / 'build'
            build.mkdir()
            for name in e2.EXECUTABLES:
                shutil.copy2(NATIVE, build / name)
            manifest = build / 'manifest.json'
            build_record = dict(out_of_tree=True, executable_sha256=e2.hash_files(
                [build / name for name in e2.EXECUTABLES]))
            manifest.write_text(json.dumps(build_record))
            evidence = root / 'review.md'
            evidence.write_text('Synthetic schema fixture only; no scientific acceptance')
            destination = output(root, sid, 'reader_fixture')
            with patch.object(e2, 'clean_tree'), patch.object(e2, 'check_build',
                    return_value=(build_record, manifest)), patch.object(e2, 'sources', return_value={}), \
                    patch.object(transfer, 'reference', return_value=(self.record, self.parents)):
                plan = transfer.prepare(root, destination, sid, 3000, evidence, smoke=False)
                plan['histories'] = [synthetic_segment(entry, destination) for entry in plan['histories']]
                plan_path = destination / 'plan.json'
                plan_path.write_text(json.dumps(plan))
                histories = []
                for entry in plan['histories']:
                    prefix = entry['output_prefix']
                    complete = Path(prefix).parent / 'complete.json'
                    complete.write_text(json.dumps(dict(status='validated', end_step=8003000,
                        plan_sha256=e2.campaign.sha256(plan_path))))
                    histories.append(dict(replica=entry['replica'], prefix=prefix, end_step=8003000,
                        chemistry_seed=entry['chemistry_seed'], physics=entry['physics'],
                        lineage=entry['lineage'], sha256=e2.hash_files(
                            [Path(prefix + suffix) for suffix in e2.validation.OUTPUTS] + [complete, plan_path])))
                record = dict(schema_version=1, stage='E2_acceptance',
                    bank_id=e2.campaign.e2_bank_id(plan['system']), provenance_kind='E2_G1_segment',
                    status='accepted_with_qualification', reviewer='in-memory CPU fixture', reviewed_at='test',
                    evidence=str(evidence), evidence_sha256=e2.campaign.sha256(evidence),
                    source_plan=str(plan_path), source_plan_sha256=e2.campaign.sha256(plan_path),
                    histories=histories, permitted_use='production_initial_state', permitted_systems=[sid],
                    qualification='Synthetic schema fixture only', numerical_qualification='test',
                    publisher_git_sha=e2.campaign.git_sha())
                registry.exclusive_validate(record, [e2.system_by_id(sid)])
                for mutation in ('lineage', 'system'):
                    bad = copy.deepcopy(record)
                    if mutation == 'lineage':
                        bad['histories'][0]['lineage']['parent_chemistry_seed'] += 1
                        systems = [e2.system_by_id(sid)]
                    else:
                        bad['permitted_systems'] = [transfer.TARGETS[1]]
                        systems = [e2.system_by_id(transfer.TARGETS[1])]
                    with self.assertRaises(ValueError):
                        registry.exclusive_validate(bad, systems)
                self.assertFalse((root / 'banks/e2_acceptance').exists())


if __name__ == '__main__':
    unittest.main()
