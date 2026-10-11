"""E2-G1 deterministic fixtures; no GPU trajectory or statistical convergence claim."""

import copy
import json
import math
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import kg_assoc_campaign as campaign
import kg_assoc_e2 as runner
import kg_assoc_e2_registry as registry
import kg_assoc_e2_validate as validation
import analyze_e2_segment as review


def fixture(root, f=3, n=10, rho=.8, ee=8, start=0, ea=4, parent_ea=4):
    system = dict(next(s for s in campaign.campaign_systems() if s['system_id'] ==
                       'F03_N010_RP080_EE08_EA04'), f=f, N=n, rho_p=rho, Ee=ee, number_of_stars=16)
    system['system_id'] = campaign.system_id(system)
    geometry = campaign.expected_geometry(system)
    length = geometry['target_volume'] ** (1 / 3)
    lines = [f"{geometry['total_beads']} atoms", f'{16*f*n} bonds', '3 atom types', '1 bond types']
    lines += [f'{-length/2:.17g} {length/2:.17g} {axis}lo {axis}hi' for axis in 'xyz']
    lines += ['Masses', '1 1', '2 1', '3 1', 'Atoms # molecular']
    vectors = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    bonds = []
    # Overlapping stars deliberately make this bookkeeping, not a physical preparation fixture.
    for star in range(16):
        center = star * (1 + f*n) + 1
        lines.append(f'{center} {star+1} 1 {star*.1:.17g} 0 0')
        for arm in range(f):
            previous = center
            for bead in range(1, n+1):
                atom = center + arm*n + bead
                point = [star*.1 + .8*bead*vectors[arm][0], .8*bead*vectors[arm][1],
                         .8*bead*vectors[arm][2]]
                lines.append(f"{atom} {star+1} {2 if bead == n else 1} " + ' '.join(map(str, point)))
                bonds.append(f'{len(bonds)+1} 1 {previous} {atom}')
                previous = atom
    lines += [f'{atom} {atom} 3 0 0 0' for atom in range(geometry['polymer_beads']+1, geometry['total_beads']+1)]
    lines += ['Velocities'] + [f'{atom} 1 1 1' for atom in range(1, geometry['total_beads']+1)]
    lines += ['Bonds'] + bonds
    body = '\n'.join(lines) + '\n'
    parent_prefix = root / 'parent/state'
    parent_prefix.parent.mkdir(parents=True)
    parent_snapshot = Path(str(parent_prefix) + ('.restart.lammpsdat' if start else '.e1.lammpsdat'))
    parent_snapshot.write_text(f'Fixture step {start}\n' + body)
    prefix = root / 'attempt/r001/state'
    prefix.parent.mkdir(parents=True)
    physics = validation.physics(system, ea)
    pair = (n+1, (1+f*n)+n+1)
    seed, md_seed = 420001, 520001
    end = start + 12000
    def sidecar(step, old_ea, creations, breaks, pairs):
        fields = dict(completed_steps=step, **dict(physics, Ea=old_ea), seed=seed, creations=creations, breaks=breaks)
        return ('KG_ASSOC_RESTART 1\n' + '\n'.join(f'{key} {value}' for key, value in fields.items()) +
                f'\nactive_bonds {len(pairs)}\n' + ''.join(f'{a} {b}\n' for a, b in pairs) + 'end\n')
    if start:
        Path(str(parent_prefix) + '.assoc_restart').write_text(sidecar(start, parent_ea, 1, 0, [pair]))
    parent = dict(kind='e2' if start else 'e1', snapshot=str(parent_snapshot), prefix=str(parent_prefix),
                  sha256=runner.hash_files([parent_snapshot] +
                           ([Path(str(parent_prefix) + '.assoc_restart')] if start else [])))
    entry = dict(replica=1, system=system, parent=parent, physics=physics, parent_Ea=parent_ea,
                 start_step=start, end_step=end, chemistry_seed=seed, md_seed=md_seed,
                 effective_md_seed=validation.effective_md_seed(md_seed), output_prefix=str(prefix))
    metadata = dict(physics, T=1, seed=seed, md_seed=md_seed, input_file=str(parent_snapshot),
                    diagnostic_every=1000, total_requested_steps=end, start_step=start,
                    total_particles=geometry['total_beads'], stickers=16*f, permanent_bonds=16*f*n,
                    ea_switch=int(ea != parent_ea), parent_Ea=parent_ea, chemistry_sweeps=120,
                    candidate_sticker_pairs=240, original_lammps_atom_ids='1_based')
    metadata.pop('temperature')
    header = '# ' + ' '.join(f'{key}={value}' for key, value in metadata.items()) + '\n'
    events = ([(start+100, 'B'), (start+1100, 'C')] if start else
              [(100, 'C'), (1100, 'B'), (2100, 'C')])
    rows = []
    observations = 0
    for step in range(start, end+1, 1000):
        creations = (1 if start else 0) + sum(kind == 'C' and event_step <= step for event_step, kind in events)
        breaks = sum(kind == 'B' and event_step <= step for event_step, kind in events)
        active = creations - breaks
        if step > start:
            observations += active
        graph = validation.analysis.topology.frame_observables(0, step, step*.01,
                        [(pair[0], pair[1], 1, 2)] if active else [],
                        validation.analysis.topology.read_system(str(parent_snapshot), 2))
        row = [step, step*.01, 16*f-2*active, active, creations, breaks, 0, active,
               2*active/(16*f), 16-active, 2 if active else 1, (2 if active else 1)/16,
               2*active/16, 2*active/16, 0, 0, observations, .1 if observations else 0, 0, 0, 0]
        rows.append(' '.join(map(str, row)))
    Path(str(prefix)+'.state').write_text(header + '# '+validation.analysis.stationarity.COLUMNS+'\n'+'\n'.join(rows)+'\n')
    Path(str(prefix)+'.events').write_text(header + ''.join(
        f'{step} {kind} {pair[0]} {pair[1]} 1 2\n' for step, kind in events))
    for suffix in ('.restart.lammpsdat', '.final_permanent.lammpsdat'):
        Path(str(prefix)+suffix).write_text(f'Fixture step {end}\n'+body)
    creations = (1 if start else 0) + sum(kind == 'C' for _, kind in events)
    breaks = sum(kind == 'B' for _, kind in events)
    Path(str(prefix)+'.assoc_restart').write_text(sidecar(end, ea, creations, breaks, [pair]))
    Path(str(prefix)+'.final_associations').write_text(f'{pair[0]} {pair[1]} 1 2\n')
    Path(str(prefix)+'.numerics.tsv').write_text(
        '# step time kinetic_energy temperature min_permanent_bond max_permanent_bond\n'+
        '\n'.join(f"{step} {step*.01} {1.5*geometry['total_beads']} 1 .8 .8"
                  for step in range(start, end+1, 1000))+'\n')
    rg2, r2 = validation.snapshot_conformation(parent_snapshot, f)
    Path(str(prefix)+'.conformation.tsv').write_text('# step time mean_rg2 mean_center_terminal_r2\n'+
        '\n'.join(f'{step} {step*.01} {rg2} {r2}' for step in range(start, end+1, 1000))+'\n')
    (prefix.parent/'stderr.log').write_text(
        f"[E2 MD stream] requested_seed={md_seed} effective_seed={entry['effective_md_seed']} internal_start_step=0\n"+
        '\n'.join(f'[VerletNVT::GronbechJensen] {field}: {value}' for field, value in
                  (('Temperature', '1.000000'), ('Time step', '0.010000'), ('Friction', '0.500000'))))
    Path(str(prefix)+'.candidate_validation.tsv').write_text(
        '# step candidates oracle_verified_active_candidates\n'+
        '\n'.join(f'{step} 2 1' for step in range(start+100, end+1, 100))+'\n')
    return entry


class E2G1Tests(unittest.TestCase):
    def test_forced_build_evidence_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / 'stdout.log'
            log.write_text('forced rebuild evidence')
            binaries = {str((runner.HERE.parent / name).resolve()): campaign.sha256(
                runner.HERE.parent / name) for name in runner.BUILD_TARGETS}
            record = dict(schema_version=1, status='built', git_sha=campaign.git_sha(),
                          source_sha256=runner.sources(), executable_sha256=binaries,
                          build_log_sha256=runner.hash_files([log]))
            runner.exclusive_json(root / 'manifest.json', record)
            with self.assertRaises(ValueError):
                runner.check_build(None)
            self.assertEqual(runner.check_build(root)[0], record)
            log.write_text('tampered evidence')
            with self.assertRaises(ValueError):
                runner.check_build(root)
            log.write_text('forced rebuild evidence')
            record['git_sha'] = '0' * 40
            (root / 'manifest.json').write_text(json.dumps(record))
            with self.assertRaises(ValueError):
                runner.check_build(root)

    def test_non_c1_geometry_and_inherited_switch_validation(self):
        for f, n, rho, ee in ((3, 10, .8, 6), (6, 10, .8, 12), (4, 20, .8, 8),
                               (4, 40, .8, 8), (4, 10, .2, 8)):
            with self.subTest(f=f, n=n, rho=rho), tempfile.TemporaryDirectory() as temp:
                entry = fixture(Path(temp), f, n, rho, ee)
                rows, events, result = validation.validate(entry, oracle=True)
                self.assertEqual(result['samples'], 13)
                self.assertEqual(result['final_bonds'], 1)
                self.assertEqual(result['oracle_sweeps'], 120)
                self.assertGreater(rows[-1]['mean_rg2'], 0)
        with tempfile.TemporaryDirectory() as temp:
            entry = fixture(Path(temp), start=8000000, ea=8)
            rows, events, result = validation.validate(entry)
            self.assertEqual(rows[0]['bonds'], 1)
            self.assertEqual(events[0]['neighbor_loss'], 1)
            command = runner.command(entry, True)
            self.assertIn('--switch-ea-from', command)
            self.assertEqual(command[command.index('--Ea')+1], '8')
            wrong = copy.deepcopy(entry)
            wrong['parent_Ea'] = 6
            with self.assertRaisesRegex(ValueError, 'physics mismatch'):
                validation.validate(wrong)

    def test_wrong_events_time_seeds_conformation_and_missing_oracle(self):
        mutations = [('.events', '2100 C', '2100 B'),
                     ('.state', 'md_seed=520001', 'md_seed=520002'),
                     ('.state', 'Ee=8', 'Ee=6'),
                     ('.conformation.tsv', '12000 120.0', '12001 120.0'),
                     ('.candidate_validation.tsv', '200 2 1\n', '')]
        for suffix, original, replacement in mutations:
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as temp:
                entry = fixture(Path(temp))
                path = Path(entry['output_prefix']+suffix)
                self.assertIn(original, path.read_text())
                path.write_text(path.read_text().replace(original, replacement))
                with self.assertRaises((ValueError, KeyError)):
                    validation.validate(entry, oracle=True)

    def test_parent_identity_and_final_permanent_state_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            entry = fixture(Path(temp))
            runner.check_hashes(entry['parent']['sha256'])
            path = Path(entry['parent']['snapshot'])
            path.write_text(path.read_text().replace('Fixture', 'Changed'))
            with self.assertRaisesRegex(ValueError, 'authenticated file changed'):
                runner.check_hashes(entry['parent']['sha256'])
        with tempfile.TemporaryDirectory() as temp:
            entry = fixture(Path(temp))
            path = Path(entry['output_prefix']+'.restart.lammpsdat')
            path.write_text(path.read_text().replace('1 1 1 0 0 0', '1 9 1 0 0 0'))
            with self.assertRaises(ValueError):
                validation.validate(entry)

    def test_all_new_bank_chemical_seeds_and_kernel_seed_query(self):
        seeds = [seed for values in runner.seed_map().values() for seed in values]
        self.assertEqual(len(seeds), 33)
        self.assertEqual(len(set(seeds)), len(seeds))
        self.assertFalse(set(seeds) & {22001, 22002, 22003})
        for seed in (32001, 520001, 520002, 520003, 520100):
            actual = subprocess.check_output([str(campaign.HERE.parent/'kg_assoc_stars'), '--md-seed-info',
                                              str(seed)], text=True).strip()
            self.assertEqual(int(actual), validation.effective_md_seed(seed))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = runner.allocate_md_seeds(root)
            path = root/'banks/e2_attempts/bank/attempt/plan.json'
            runner.exclusive_json(path, dict(histories=[dict(md_seed=seed,
                                  effective_md_seed=validation.effective_md_seed(seed)) for seed in first]))
            second = runner.allocate_md_seeds(root)
            self.assertFalse(set(first) & set(second))

    def test_approval_dry_run_no_overwrite_and_fail_fast(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempt = root/'attempt'
            entries = [dict(replica=replica, command=['never-execute'], output_prefix=str(attempt/f'r{replica:03d}/state'),
                            parent=dict(sha256={})) for replica in (1, 2, 3)]
            for entry in entries:
                Path(entry['output_prefix']).parent.mkdir(parents=True)
            plan = dict(histories=entries, smoke=True)
            runner.exclusive_json(attempt/'plan.json', plan)
            with mock.patch.object(runner, 'check_plan', return_value=plan), mock.patch.object(runner.subprocess, 'Popen') as proc:
                runner.launch(root, attempt)
                proc.assert_not_called()
                with self.assertRaisesRegex(ValueError, 'approval'):
                    runner.launch(root, attempt, True)
                approval = attempt/'approval.json'
                runner.exclusive_json(approval, dict(schema_version=1, approved=True, purpose='e2_smoke',
                                      reviewer='fixture', approved_at='test', plan_sha256=campaign.sha256(attempt/'plan.json')))
                proc.return_value.wait.return_value = 1
                with mock.patch.object(runner.subprocess, 'check_output', return_value='fixture GPU'):
                    with self.assertRaisesRegex(ValueError, 'MD executable failed'):
                        runner.launch(root, attempt, True, approval)
                self.assertEqual(proc.call_count, 1)
                self.assertTrue((attempt/'r001/incomplete.json').exists())
                self.assertFalse(any((attempt/'r002').iterdir()))
                with self.assertRaisesRegex(ValueError, 'already used'):
                    runner.launch(root, attempt)
            with self.assertRaises(FileExistsError):
                runner.exclusive_json(attempt/'plan.json', {})
            self.assertFalse((attempt/'.launch.lock').exists())

    def test_approval_hash_and_smoke_parent_gates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runner.exclusive_json(root/'plan.json', {})
            runner.exclusive_json(root/'approval.json', dict(schema_version=1, approved=True, reviewer='reviewer',
                                  approved_at='date', purpose='e2_segment', plan_sha256='wrong'))
            with self.assertRaisesRegex(ValueError, 'invalid approval'):
                runner.approval_record(root/'approval.json', root/'plan.json', 'e2_segment')
            with self.assertRaisesRegex(ValueError, 'matching capped'):
                runner.matching_smoke(root, None, {})
            plan = dict(smoke=True, steps=10000, git_sha='sha', executable_sha256={}, source_sha256={},
                        histories=[dict(physics={}, parent=dict(sha256={'parent':'old'}), chemistry_seed=1, parent_Ea=4)])
            long = copy.deepcopy(plan)
            long['histories'][0]['parent']['sha256']['parent'] = 'different'
            with mock.patch.object(runner, 'verify', return_value=plan):
                with self.assertRaisesRegex(ValueError, 'parent/chemistry'):
                    runner.matching_smoke(root, root, long)

    def test_generalized_exact_exposure_and_constant_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            entry = fixture(Path(temp))
            rows, events, _ = validation.validate(entry)
            first = review.review.window(rows, events, 0, 4000, stickers=48, stars=16,
                                         metrics=review.METRICS)
            self.assertEqual(first['duration'], 40)
            self.assertEqual(first['event_counts']['creations'], 2)
            self.assertEqual(first['exposure']['active_bond_time'], 29)
            self.assertEqual(first['exposure']['free_sticker_time'], 48*40-2*29)
            self.assertAlmostEqual(first['event_rates_per_star_time']['creations'], 2/(16*40))
            self.assertIn('mean_rg2', first['metrics'])

    def test_prepare_manifest_dry_run_and_analysis_pipeline(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture_entries = [fixture(root/f'h{replica}') for replica in (1, 2, 3)]
            system = fixture_entries[0]['system']
            campaign.write_json(root/'campaign_protocol.json', campaign.load_json(campaign.PROTOCOL_PATH))
            campaign.write_json(root/'manifest.json', dict(systems=[s['system_id'] for s in campaign.campaign_systems()]))
            evidence = root/'review.md'
            evidence.write_text('fixture E1 review')
            attempt = root/'banks/e2_attempts'/campaign.e2_bank_id(system)/'probe_v1'
            def source(_root, _system, replica):
                return fixture_entries[replica-1]['parent']
            with mock.patch.object(runner, 'live_code'), \
                    mock.patch.object(runner, 'system_by_id', return_value=system), \
                    mock.patch.object(runner, 'original_e1', side_effect=source), \
                    mock.patch.object(runner, 'check_build', return_value=({}, evidence)):
                plan = runner.prepare(root, attempt, system['system_id'], 12000, evidence)
                self.assertEqual(plan['segment_index'], 1)
                self.assertEqual(plan['preparation_Ea'], 4)
                runner.launch(root, attempt)
                with self.assertRaisesRegex(ValueError, 'NEW direct attempt'):
                    runner.prepare(root, attempt, system['system_id'], 12000, evidence)
                for entry, origin in zip(plan['histories'], fixture_entries):
                    prefix = entry['output_prefix']
                    for suffix in validation.OUTPUTS:
                        text = Path(origin['output_prefix']+suffix).read_text()
                        text = text.replace('seed=420001', f"seed={entry['chemistry_seed']}")
                        text = text.replace('seed 420001', f"seed {entry['chemistry_seed']}")
                        text = text.replace('md_seed=520001', f"md_seed={entry['md_seed']}")
                        Path(prefix+suffix).write_text(text)
                    log = Path(origin['output_prefix']).parent/'stderr.log'
                    text = log.read_text().replace('requested_seed=520001', f"requested_seed={entry['md_seed']}")
                    text = text.replace(str(origin['effective_md_seed']), str(entry['effective_md_seed']))
                    (Path(prefix).parent/'stderr.log').write_text(text)
                    _, _, checked = validation.validate(entry)
                    runner.exclusive_json(Path(prefix).parent/'complete.json', dict(
                        status='validated', plan_sha256=campaign.sha256(attempt/'plan.json'),
                        output_sha256=runner.hash_files(Path(prefix).parent.iterdir())))
                runner.verify(root, attempt)
                first = root/'aggregate/e2/review_v1'
                second = root/'aggregate/e2/review_v2'
                review.analyze(root, attempt, first, 4000)
                review.analyze(root, attempt, second, 4000)
                self.assertEqual((first/'summary.json').read_bytes(), (second/'summary.json').read_bytes())
                summary = campaign.load_json(first/'summary.json')
                self.assertFalse(summary['automatic_acceptance'])
                self.assertEqual(summary['comparisons'][0]['replicas'], 3)
                self.assertTrue(summary['records'][0]['windows'][0]['metrics']['mean_rg2']['constant_not_mixing_evidence'])
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    review.analyze(root, attempt, first, 4000)
                extension = attempt.parent/'extension_v2'
                extended = runner.prepare(root, extension, system['system_id'], 4000, evidence,
                                          parent_attempt=attempt)
                runner.check_plan(root, extension)
                self.assertEqual(extended['segment_index'], 2)
                for old, new in zip(plan['histories'], extended['histories']):
                    self.assertEqual(new['start_step'], old['end_step'])
                    self.assertEqual(new['chemistry_seed'], old['chemistry_seed'])
                    self.assertNotEqual(new['effective_md_seed'], old['effective_md_seed'])
                    self.assertIn('--restart-prefix', new['command'])
                    self.assertNotIn('--switch-ea-from', new['command'])
                manifest = campaign.load_json(attempt/'plan.json')
                manifest['histories'][0]['command'] += ['--force']
                (attempt/'plan.json').write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, 'command/physics/seed'):
                    runner.check_plan(root, attempt)

    def test_arbitrary_segment_endpoint_and_host_switch_front_end(self):
        self.assertEqual(validation.diagnostic_steps(1250, 4251), [1250, 2000, 3000, 4000, 4251])
        with tempfile.TemporaryDirectory() as temp:
            entry = fixture(Path(temp), start=8000000, ea=8)
            exe = campaign.HERE.parent/'kg_assoc_campaign_production'
            arguments = [str(exe), '--equilibrated-prefix', entry['parent']['prefix'], '--Ea', '8',
                         '--Ee', '8', '--seed', '701001', '--output', str(Path(temp)/'never'),
                         '--validate-initial-state']
            positive = subprocess.run(arguments+['--switch-ea-from', '4'], text=True, capture_output=True)
            self.assertEqual(positive.returncode, 0, positive.stderr)
            self.assertIn('target_Ea=8', positive.stdout)
            for flags in ([], ['--switch-ea-from', '6']):
                negative = subprocess.run(arguments+flags, text=True, capture_output=True)
                self.assertNotEqual(negative.returncode, 0)
            self.assertFalse((Path(temp)/'never').exists())

    def test_non_aligned_final_endpoint_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            entry = fixture(Path(temp))
            prefix = entry['output_prefix']
            entry['end_step'] = 12001
            for suffix in ('.state', '.events'):
                path = Path(prefix+suffix)
                path.write_text(path.read_text().replace('total_requested_steps=12000', 'total_requested_steps=12001'))
            for suffix in ('.state', '.numerics.tsv', '.conformation.tsv'):
                path = Path(prefix+suffix)
                fields = path.read_text().splitlines()[-1].split()
                fields[:2] = ['12001', '120.01']
                if suffix == '.state':
                    fields[16] = str(int(fields[16])+1)
                path.write_text(path.read_text()+' '.join(fields)+'\n')
            for suffix in ('.restart.lammpsdat', '.final_permanent.lammpsdat'):
                path = Path(prefix+suffix)
                path.write_text(path.read_text().replace('step 12000', 'step 12001'))
            path = Path(prefix+'.assoc_restart')
            path.write_text(path.read_text().replace('completed_steps 12000', 'completed_steps 12001'))
            rows, _, result = validation.validate(entry, oracle=True)
            self.assertEqual(rows[-1]['step'], 12001)
            self.assertEqual(result['samples'], 14)

    def test_legacy_execution_dirty_source_and_cross_bank_rejection(self):
        arguments = campaign.build_parser().parse_args(['equilibrate', '--stage', 'e2',
                    '--dataset-root', '/never', '--execute'])
        with self.assertRaisesRegex(ValueError, 'generic E2 execution is disabled'):
            campaign.command_equilibrate(arguments)
        with mock.patch.object(runner.subprocess, 'check_output', return_value=' M source.cu'):
            with self.assertRaisesRegex(ValueError, 'commit source changes'):
                runner.live_code()
        record = dict(permitted_systems=['F03_N010_RP080_EE08_EA04'], permitted_use='production_initial_state')
        with self.assertRaisesRegex(ValueError, 'does not permit'):
            registry.permitted(record, runner.system_by_id('F06_N010_RP080_EE08_EA04'))

    def test_registry_mandatory_missing_acceptance_and_explicit_switch_command(self):
        system = runner.system_by_id('F04_N010_RP080_EE08_EA08')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, '--e2-registry'):
                registry.resolve(root, None, system, 1)
            path = root/'banks/e2_registry/version.json'
            runner.exclusive_json(path, dict(schema_version=1, stage='E2_active_registry', systems={}))
            with self.assertRaisesRegex(ValueError, 'acceptance absent'):
                registry.resolve(root, path, system, 1)
            args = campaign.build_parser().parse_args(['prepare-production', '--dataset-root', str(root),
                             '--system', system['system_id']])
            with self.assertRaisesRegex(ValueError, '--e2-registry'):
                campaign.command_prepare_production(args)
            self.assertFalse((root/'systems').exists())
        run = dict(replica=1, md_seed=701001, parent_e2='/accepted/8M/state', active_e2=dict(parent_Ea=4))
        command = campaign.production_command(Path('/dataset'), system, run)
        self.assertEqual(command[command.index('--switch-ea-from')+1], '4')

    def test_registry_publication_authentication_and_use_restrictions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entry = fixture(root)
            system = entry['system']
            evidence = root/'review.md'
            evidence.write_text('fixture human decision')
            plan = root/'source_plan.json'
            runner.exclusive_json(plan, {})
            histories = []
            for replica in (1, 2, 3):
                prefix = root/f'accepted/r{replica:03d}/state'
                prefix.parent.mkdir(parents=True)
                for suffix in validation.OUTPUTS:
                    Path(str(prefix)+suffix).write_bytes(Path(entry['output_prefix']+suffix).read_bytes())
                sidecar = Path(str(prefix)+'.assoc_restart')
                sidecar.write_text(sidecar.read_text().replace('seed 420001', f'seed {420000+replica}'))
                histories.append(dict(replica=replica, prefix=str(prefix), end_step=12000,
                                      chemistry_seed=420000+replica, physics=entry['physics'],
                                      sha256=runner.hash_files([Path(str(prefix)+s) for s in validation.OUTPUTS])))
            plan.write_text(json.dumps(dict(stage='E2-G1', smoke=False, histories=[dict(
                output_prefix=item['prefix'], end_step=item['end_step'], physics=item['physics'],
                chemistry_seed=item['chemistry_seed']) for item in histories])))
            for item in histories:
                complete = Path(item['prefix']).parent/'complete.json'
                runner.exclusive_json(complete, dict(status='validated', plan_sha256=campaign.sha256(plan)))
                item['sha256'][str(complete)] = campaign.sha256(complete)
            record = dict(schema_version=1, stage='E2_acceptance', provenance_kind='E2_G1_segment', bank_id=campaign.e2_bank_id(system),
                          status='accepted', reviewer='fixture', reviewed_at='test', evidence=str(evidence),
                          evidence_sha256=campaign.sha256(evidence), source_plan=str(plan), source_plan_sha256=campaign.sha256(plan),
                          histories=histories, permitted_use='production_initial_state', permitted_systems=[system['system_id']],
                          qualification='', numerical_qualification='fixture qualification',
                          publisher_git_sha=campaign.git_sha())
            path = root/'banks/e2_acceptance/record.json'
            runner.exclusive_json(path, record)
            active = root/'banks/e2_registry/version.json'
            with mock.patch.object(runner, 'system_by_id', return_value=system):
                registry.publish(root, active, [path])
                resolved = registry.resolve(root, active, system, 2)
                self.assertEqual(resolved['prefix'], histories[1]['prefix'])
                with self.assertRaisesRegex(ValueError, 'new registry'):
                    registry.publish(root, active, [path])
                record['reviewer'] = 'changed'
                path.write_text(json.dumps(record))
                with self.assertRaisesRegex(ValueError, 'acceptance changed'):
                    registry.resolve(root, active, system, 1)


if __name__ == '__main__':
    unittest.main()
