"""Scientific/data-integrity regression fixtures; no GPU or simulation code calls."""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import catalog
from catalog_model import Catalog, Reader, campaign_systems, discover, geometry_id

HERE = Path(__file__).resolve().parent
WEAK = 'F04_N010_RP080_EE04_EA04'
C1 = 'F04_N010_RP080_EE08_EA04'


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.root = self.repo / 'examples/KG_Assoc/kg_assoc_100m'
        self.root.mkdir(parents=True)
        self.inventory = self.repo / 'examples/KG_Assoc/campaign/e2_remaining_inventory_20261011.json'
        self.write(self.inventory, dict(schema_version=1, e1_states=[], C1_recovery=[], preserved_files={}))
        self.write(self.root / 'manifest.json', dict(schema_version=1,
                   systems=[s['system_id'] for s in campaign_systems()]))
        for system in campaign_systems():
            self.write(self.root / 'systems' / system['system_id'] / 'system.json', system)

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding='utf-8')
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def scan(self, registry=None):
        return Catalog(self.repo, self.root, registry).scan()

    def codes(self, graph):
        return {d['code'] for d in graph['diagnostics']}

    def plan(self, name='first', smoke=False, complete=3, parent=None, start=0, seed=410001, md=510001):
        system = next(s for s in campaign_systems() if s['system_id'] == WEAK)
        directory = self.root / 'banks/e2_attempts/F04_N010_RP080_EE04' / name
        histories = []
        for replica in (1, 2, 3):
            prefix = str(directory / f'r{replica:03d}/state')
            parent_data = dict(kind='e1', snapshot=str(self.root / f'banks/e1/F04_N010_RP080/r{replica:03d}/state.e1.lammpsdat'), sha256={})
            if parent:
                parent_data = dict(kind='e2', prefix=str(parent / f'r{replica:03d}/state'), sha256={})
            histories.append(dict(replica=replica, output_prefix=prefix, parent=parent_data,
                start_step=start, end_step=start + 10000, chemistry_seed=seed + replica,
                md_seed=md + replica, effective_md_seed=md + replica + 1000,
                physics=dict(arms=4, narm=10, Ee=4, Ea=4, dt=.01, temperature=1), parent_Ea=4))
        data = dict(schema_version=1, stage='E2-G1', system=system, dataset_root=str(self.root),
                    smoke=smoke, steps=10000, histories=histories, git_sha='a' * 40)
        digest = self.write(directory / 'plan.json', data)
        self.write(directory / 'approval.json', dict(schema_version=1, approved=True, plan_sha256=digest,
                   purpose='e2_smoke' if smoke else 'e2_segment', scientific_equilibrium_acceptance=False))
        for history in histories:
            base = Path(history['output_prefix']).parent
            self.write(base / 'started.json', dict(plan_sha256=digest, host='remote_gpu', pid=99999,
                       started_at='2000-01-01T00:00:00+00:00'))
            if history['replica'] <= complete:
                self.write(base / 'complete.json', dict(status='validated', plan_sha256=digest,
                    end_step=history['end_step'], validation=dict(numerical_status='valid')))
        return directory

    def acceptance(self, directory, name='acceptance'):
        plan = json.loads((directory / 'plan.json').read_text())
        histories = []
        for h in plan['histories']:
            entry = {k: h[k] for k in ('replica', 'output_prefix', 'end_step', 'chemistry_seed', 'physics')}
            entry['prefix'] = entry.pop('output_prefix')
            hashes = {}
            for suffix in ('.restart.lammpsdat', '.assoc_restart'):
                path = Path(entry['prefix'] + suffix)
                path.write_text('payload deliberately not authenticated')
                hashes[str(path)] = '0' * 64
            receipt = Path(entry['prefix']).parent / 'complete.json'
            hashes[str(receipt)] = hashlib.sha256(receipt.read_bytes()).hexdigest()
            entry['sha256'] = hashes
            histories.append(entry)
        review = self.root / 'aggregate/review/SCIENTIFIC_REVIEW.md'
        review.parent.mkdir(parents=True, exist_ok=True)
        review.write_text('Explicit reviewer evidence')
        data = dict(schema_version=1, stage='E2_acceptance', bank_id='F04_N010_RP080_EE04',
            provenance_kind='E2_G1_segment', status='accepted', reviewer='scientist', reviewed_at='now',
            evidence=str(review), evidence_sha256='0' * 64, source_plan=str(directory / 'plan.json'),
            source_plan_sha256=hashlib.sha256((directory / 'plan.json').read_bytes()).hexdigest(),
            histories=histories, permitted_use='production_initial_state', permitted_systems=[WEAK],
            qualification='', numerical_qualification='full integrator invariance unproven', publisher_git_sha='a' * 40)
        path = self.root / 'banks/e2_acceptance' / (name + '.json')
        digest = self.write(path, data)
        return path, digest

    def test_discovery_independent_of_cwd_and_environment(self):
        with patch.dict('os.environ', {'DATASET_ROOT': '/wrong'}):
            repo, root = discover(self.repo / 'examples/KG_Assoc/campaign/catalog.py')
        self.assertEqual(repo, self.repo)
        self.assertEqual(root, self.root)

    def test_23_conditions_69_slots_24_shared_starts_without_runtime(self):
        graph = self.scan()
        self.assertEqual(len(graph['systems']), 23)
        self.assertEqual(len(graph['histories']), 69)
        self.assertEqual(graph['coverage']['unique_selected_e1'], 24)
        controls = [s for s in graph['systems'] if not s['bank']]
        self.assertEqual(len(controls), 8)
        self.assertTrue(all(s['selection'] == 'E2_not_applicable' for s in controls))

    def test_active_E1_retry_selected_without_promoting_original(self):
        selected = 'banks/e1_retries/F04_N010_RP060/r002/attempt001'
        self.write(self.root / 'banks/e1/active_states.json', {'F04_N010_RP060/r002': selected})
        graph = self.scan()
        histories = [h for h in graph['histories'] if 'RP060' in h['id'] and h['replica'] == 2]
        self.assertTrue(all(h['selected_e1'] == selected for h in histories))
        self.assertTrue(all(h['e1_scientific'] == 'review_required' for h in histories))

    def test_smoke_success_never_equilibrium_or_production_authorization(self):
        self.plan(smoke=True)
        graph = self.scan()
        self.assertTrue(all(a['scientific'] == 'not_applicable_for_equilibrium' for a in graph['attempts']))
        system = catalog.system_record(graph, WEAK)['system']
        self.assertEqual(system['scientific'], 'absent')
        self.assertEqual(system['production_authorization'], 'absent')

    def test_partial_failed_and_remote_liveness_not_inferred(self):
        directory = self.plan(complete=1)
        self.write(directory / 'r002/incomplete.json', dict(error='retained failure'))
        graph = self.scan()
        states = [a['execution'] for a in graph['attempts']]
        self.assertEqual(states, ['completed_receipt', 'failed_receipt', 'started_liveness_unknown'])
        self.assertIn('stale_candidate_liveness_unknown', self.codes(graph))

    def test_completion_hash_mismatch_and_wrong_step(self):
        directory = self.plan()
        self.write(directory / 'r001/complete.json', dict(status='validated', plan_sha256='0' * 64,
                   end_step=9999, validation=dict(numerical_status='valid')))
        graph = self.scan()
        self.assertIn('completion_plan_mismatch', self.codes(graph))
        self.assertEqual(graph['attempts'][0]['numerical'], 'stale_mismatched')

    def test_approval_is_checked_and_not_created(self):
        directory = self.plan()
        self.write(directory / 'approval.json', dict(approved=True, plan_sha256='wrong'))
        graph = self.scan()
        self.assertIn('authorization_mismatch', self.codes(graph))
        self.assertTrue(all(a['authorization'] == 'absent_or_mismatched' for a in graph['attempts']))

    def test_extension_seed_and_absolute_step_continuity(self):
        first = self.plan()
        self.plan('extension', parent=first, start=10000, md=520001)
        graph = self.scan()
        self.assertNotIn('step_discontinuity', self.codes(graph))
        self.assertNotIn('chemical_rng_changed', self.codes(graph))
        self.assertNotIn('MD_seed_not_reseeded', self.codes(graph))
        self.assertEqual(sum(bool(a['parent_segment']) for a in graph['attempts']), 3)

    def test_bad_extension_rng_steps_and_missing_parent(self):
        first = self.plan()
        self.plan('extension', parent=first, start=9999, seed=500000)
        self.plan('orphan', parent=self.root / 'absent', start=10000)
        codes = self.codes(self.scan())
        self.assertTrue({'step_discontinuity', 'chemical_rng_changed', 'MD_seed_not_reseeded',
                         'unresolved_parent_segment'} <= codes)

    def test_lineage_cycles_and_forks_visible(self):
        first = self.plan()
        self.plan('extension', parent=first, start=10000, md=520001)
        self.plan('fork', parent=first, start=10000, md=530001)
        self.assertIn('lineage_fork', self.codes(self.scan()))
        data = json.loads((first / 'plan.json').read_text())
        data['histories'][0]['parent'] = dict(kind='e2', prefix=data['histories'][0]['output_prefix'])
        self.write(first / 'plan.json', data)
        self.assertIn('lineage_cycle', self.codes(self.scan()))

    def test_duplicate_fresh_chemical_seeds_diagnosed(self):
        self.plan('one')
        self.plan('two')
        self.assertIn('chemical_seed_collision', self.codes(self.scan()))

    def test_C1_defective_and_corrected_and_documented_not_formal(self):
        historical = 'banks/e2/F04_N010_RP080_EE08/r001/command.json'
        self.write(self.root / historical, dict(schema_version=1, replica=1, completed_e2_steps=6000000,
                                               status='finished'))
        prefix = 'banks/e2_extensions/recovery/r001/state'
        inventory = dict(schema_version=1, e1_states=[], preserved_files={historical: {'sha256': '0' * 64}},
                         C1_recovery=[dict(replica=1, prefix=prefix,
                          user_review_status='provisionally_accepted_with_slow_topology_qualification')])
        self.write(self.inventory, inventory)
        self.write(self.root / 'banks/e2_extensions/recovery/plan.json', dict(
            absolute_start_step=6000000, absolute_end_step=8000000,
            commands=[['exe', '--output', str(self.root / prefix), '--restart-prefix',
                       str(self.root / historical).replace('command.json', 'state'), '--seed', '22001', '--md-seed', '32001']]))
        self.write(self.root / 'banks/e2_extensions/recovery/r001/status.json',
                   dict(status='validated', numerical_validation={'accepted_events': 2}))
        graph = self.scan()
        roles = {a['role'] for a in graph['attempts']}
        self.assertTrue({'corrected_C1_8M', 'historical_pbc_defective_6M'} <= roles)
        system = catalog.system_record(graph, C1)['system']
        self.assertIsNotNone(system['documented_decision'])
        self.assertEqual(system['selection'], 'missing')
        self.assertFalse(graph['acceptances'])

    def test_registry_selection_explicit_and_permitted_conditions_only(self):
        directory = self.plan()
        acceptance, digest = self.acceptance(directory)
        registry = dict(schema_version=1, stage='E2_active_registry',
                        systems={WEAK: dict(acceptance=str(acceptance), sha256=digest)})
        self.write(self.root / 'banks/e2_registry/one.json', registry)
        self.write(self.root / 'banks/e2_registry/two.json', registry)
        graph = self.scan()
        self.assertIsNone(graph['selected_registry'])
        self.assertEqual(catalog.system_record(graph, WEAK)['system']['selection'], 'ambiguous')
        selected = self.scan('banks/e2_registry/one.json')
        system = catalog.system_record(selected, WEAK)['system']
        self.assertEqual(system['selection'], 'selected_metadata_payload_deferred')
        self.assertEqual(system['production_authorization'], 'absent')
        self.assertEqual(catalog.system_record(selected, C1)['system']['scientific'], 'absent')

    def test_smoke_formal_acceptance_rejected(self):
        acceptance, digest = self.acceptance(self.plan(smoke=True))
        self.write(self.root / 'banks/e2_registry/one.json', dict(schema_version=1, stage='E2_active_registry',
                   systems={WEAK: dict(acceptance=str(acceptance), sha256=digest)}))
        graph = self.scan()
        self.assertIn('acceptance_smoke_cannot_be_accepted', self.codes(graph))
        self.assertEqual(catalog.system_record(graph, WEAK)['system']['selection'], 'invalid_selection')

    def test_changed_metadata_dependency_invalidates_acceptance(self):
        directory = self.plan()
        acceptance, digest = self.acceptance(directory)
        self.write(directory / 'r001/complete.json', dict(status='validated', plan_sha256='wrong'))
        graph = self.scan()
        self.assertFalse(graph['acceptances'][0]['metadata_eligible'])
        self.assertIn('changed_metadata', self.codes(graph))

    def test_production_completion_does_not_authorize_or_accept(self):
        self.write(self.root / f'systems/{WEAK}/production/r001/run.json', dict(
            schema_version=1, system_id=WEAK, replica=1, status='complete',
            validation=dict(numerical_status='valid'), completed_production_steps=100000000))
        graph = self.scan()
        attempt = graph['attempts'][0]
        self.assertEqual(attempt['numerical'], 'recorded_pass')
        self.assertEqual(attempt['authorization'], 'legacy_execution_evidence_no_launch_receipt')
        self.assertEqual(catalog.system_record(graph, WEAK)['system']['scientific'], 'absent')

    def test_truncated_unknown_oversize_metadata_are_visible(self):
        directory = self.plan()
        (directory / 'approval.json').write_text('{')
        self.write(directory / 'r001/complete.json', dict(schema_version=999, status='validated'))
        with (directory / 'r002/complete.json').open('wb') as stream:
            stream.truncate(5 * 1024 * 1024)
        graph = self.scan()
        self.assertTrue({'unreadable_metadata', 'unsupported_schema'} <= self.codes(graph))
        self.assertNotEqual(graph['attempts'][0]['numerical'], 'recorded_pass')

    def test_path_traversal_symlink_and_external_reference(self):
        reader = Reader(self.repo, self.root)
        self.assertIsNone(reader.resolve('../escape'))
        outside = Path(self.temp.name).parent / 'outside-catalog-test'
        (self.root / 'escape.json').symlink_to(outside)
        self.assertIsNone(reader.read(self.root / 'escape.json'))
        self.assertIsNone(reader.reference('/unknown-host/file')['path'])

    def test_declared_root_relocation_without_basename_guessing(self):
        directory = self.plan()
        data = json.loads((directory / 'plan.json').read_text())
        old_root = '/gpu/checkout/examples/KG_Assoc/kg_assoc_100m'
        data['dataset_root'] = old_root
        for history in data['histories']:
            history['output_prefix'] = history['output_prefix'].replace(str(self.root), old_root)
        self.write(directory / 'plan.json', data)
        graph = self.scan()
        r = Catalog(self.repo, self.root)
        r.scan()
        self.assertEqual(r.reader.resolve(old_root + '/manifest.json'), self.root / 'manifest.json')
        self.assertIsNone(r.reader.resolve('/unmapped/manifest.json'))

    def test_runtime_tree_unchanged_and_giant_payload_never_opened(self):
        directory = self.plan()
        payload = directory / 'r001/state.events'
        with payload.open('wb') as stream:
            stream.truncate(10**10)
        original_open = Path.open
        def guarded_open(path, *args, **kwargs):
            if path.suffix in ('.events', '.state', '.bin', '.lammpsdat', '.assoc_restart'):
                raise AssertionError('Payload opened: ' + str(path))
            return original_open(path, *args, **kwargs)
        before = {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in self.root.rglob('*')}
        with patch.object(Path, 'open', guarded_open):
            graph = self.scan()
            output = catalog.publish(graph, self.repo)
        after = {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in self.root.rglob('*')}
        self.assertEqual(before, after)
        self.assertEqual(len(list((output / 'systems').glob('*.html'))), 23)

    def test_immutable_snapshots_html_escaping_and_csv_formula(self):
        directory = self.plan()
        data = json.loads((directory / 'plan.json').read_text())
        data['untrusted'] = '<script>alert(1)</script>'
        self.write(directory / 'plan.json', data)
        graph = self.scan()
        first = catalog.publish(graph, self.repo)
        before = (first / 'index.html').read_bytes()
        second = catalog.publish(graph, self.repo)
        self.assertNotEqual(first, second)
        self.assertEqual((first / 'index.html').read_bytes(), before)
        page = (first / 'systems' / (WEAK + '.html')).read_text()
        self.assertIn('&lt;script&gt;', page)
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertEqual(catalog.safe_csv('=malicious'), "'=malicious")
        self.assertNotIn('fetch(', (first / 'index.html').read_text())

    def test_end_to_end_cli_report_show_status_and_no_launch_commands(self):
        self.plan()
        with patch('catalog.discover', return_value=(self.repo, self.root)), contextlib.redirect_stdout(io.StringIO()) as output:
            catalog.main(['status'])
            catalog.main(['show', WEAK])
            catalog.main(['report'])
            catalog.main(['export', '--format', 'csv'])
        self.assertIn('Immutable snapshot', output.getvalue())
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            catalog.main(['equilibrate'])


    def test_C1_Ea_switch_must_be_explicit_in_recorded_command(self):
        directory = self.plan(smoke=True)
        data = json.loads((directory / 'plan.json').read_text())
        for h in data['histories']:
            h['parent_Ea'] = 4
            h['physics']['Ea'] = 8
            h['command'] = ['exe', '--switch-ea-from', '4', '--Ea', '8']
        self.write(directory / 'plan.json', data)
        graph = self.scan()
        self.assertNotIn('Ea_switch_not_explicit', self.codes(graph))
        self.assertEqual(graph['attempts'][0]['parameter_switch']['preparation_Ea'], 8)
        data['histories'][0]['command'] = ['exe', '--Ea', '8']
        self.write(directory / 'plan.json', data)
        self.assertIn('Ea_switch_not_explicit', self.codes(self.scan()))

    def test_changed_while_reading_and_malformed_adapter_visible(self):
        reader = Reader(self.repo, self.root)
        original_stat = Path.stat
        calls = [0]
        def changing_stat(path, *args, **kwargs):
            stat = original_stat(path, *args, **kwargs)
            if path == self.root / 'manifest.json':
                calls[0] += 1
                values = list(stat)
                values[6] += calls[0]
                return type(stat)(values)
            return stat
        with patch.object(Path, 'stat', changing_stat):
            self.assertIsNone(reader.read(self.root / 'manifest.json'))
        self.assertEqual(reader.issues[-1]['code'], 'unreadable_metadata')
        directory = self.plan()
        data = json.loads((directory / 'plan.json').read_text())
        data['histories'] = 'invalid'
        self.write(directory / 'plan.json', data)
        self.assertIn('invalid_adapter_record', self.codes(self.scan()))

    def test_failed_publication_retains_evidence_and_collision_never_overwrites(self):
        graph = self.scan()
        with patch('catalog.render_index', side_effect=OSError('renderer failed')):
            with self.assertRaises(OSError):
                catalog.publish(graph, self.repo)
        output_root = self.repo / 'examples/KG_Assoc/catalog_output'
        self.assertEqual(len(list(output_root.glob('.building_*/catalog.json'))), 1)
        with patch('catalog.utcnow', return_value='fixed'), patch('catalog.uuid.uuid4') as uuid:
            uuid.return_value.hex = 'fixed'
            first = catalog.publish(graph, self.repo)
            contents = (first / 'catalog.json').read_bytes()
            with self.assertRaises(FileExistsError):
                catalog.publish(graph, self.repo)
            self.assertEqual(contents, (first / 'catalog.json').read_bytes())

    def test_metadata_projection_deterministic_and_unknown_registry_rejected(self):
        self.plan()
        first, second = self.scan(), self.scan()
        for graph in (first, second):
            graph.pop('scan_started_at')
            graph.pop('scan_finished_at')
        self.assertEqual(first, second)
        with self.assertRaises(ValueError):
            self.scan('banks/e2_registry/absent.json')


    def test_legacy_output_hashes_are_relative_to_receipt_directory(self):
        directory = self.plan()
        payload = directory / 'r001/state.events'
        payload.write_text('do not read')
        data = json.loads((directory / 'r001/complete.json').read_text())
        data['output_sha256'] = {'state.events': '0' * 64}
        self.write(directory / 'r001/complete.json', data)
        graph = self.scan()
        ref = next(r for r in graph['references'] if r['original'] == 'state.events')
        self.assertEqual(ref['path'], str(payload))
        self.assertEqual(ref['verification'], 'payload_deferred')
        self.assertEqual(ref['integrity'], 'present_payload_deferred')


    def test_legacy_E1_and_C1_reviews_are_navigable_without_acceptance(self):
        self.write(self.root / 'aggregate/e1/review/F03_N010_RP080_r001.json',
            dict(numerical_status='valid', snapshot=dict(path=str(self.root / 'banks/e1/F03_N010_RP080/r001/state.e1.lammpsdat'))))
        self.write(self.root / 'aggregate/e2/C1_review/r001.json',
            dict(corrected=[], defective=[], replica=1))
        self.write(self.root / 'aggregate/e1/audit/runtime_checks.json', [{'result': 'recorded'}])
        graph = self.scan()
        self.assertTrue(any('F03_N010' in review['source'] for review in graph['reviews']))
        self.assertTrue(any('C1_review' in review['source'] for review in graph['reviews']))
        self.assertTrue(any(record['adapter'] == 'legacy-diagnostic-array-v1' for record in graph['records']))
        self.assertFalse(graph['acceptances'])


    def test_plan_condition_and_selected_E1_parent_disagreements(self):
        directory = self.plan()
        data = json.loads((directory / 'plan.json').read_text())
        data['system']['N'] = 40
        data['histories'][0]['parent']['snapshot'] = str(self.root / 'banks/e1/F06_N010_RP080/r001/state.e1.lammpsdat')
        self.write(directory / 'plan.json', data)
        self.assertTrue({'plan_condition_mismatch', 'physics_mismatch', 'E1_parent_not_selected'} <= self.codes(self.scan()))


    def test_documented_joint_hold_never_registers_formal_acceptance(self):
        sid = 'F04_N010_RP020_EE08_EA04'
        evidence = self.repo / 'examples/KG_Assoc/reviews/joint/summary.json'
        digest = self.write(evidence, {'scientific_status': 'review_required'})
        self.write(evidence.parent / 'decision.json', dict(schema_version=1,
            stage='E2_scientific_review_decision', formal_acceptance=False,
            evidence_sha256={'examples/KG_Assoc/reviews/joint/summary.json': digest},
            systems={sid: dict(status='acceptance_deferred_material_drift', qualification='initialization only')}))
        graph = self.scan()
        system = catalog.system_record(graph, sid)['system']
        self.assertEqual(system['scientific'], 'review_hold_material_drift')
        self.assertEqual(system['selection'], 'missing')
        self.assertEqual(system['production_authorization'], 'absent')
        self.assertFalse(graph['acceptances'])
        self.assertTrue(system['documented_reviews'])
        self.write(evidence, {'changed': True})
        self.assertIn('changed_metadata', self.codes(self.scan()))

    def test_documented_review_cannot_masquerade_as_formal_acceptance(self):
        path = self.repo / 'examples/KG_Assoc/reviews/review/decision.json'
        self.write(path, dict(schema_version=1, stage='E2_acceptance', formal_acceptance=True,
                             systems={WEAK: {'status': 'accepted'}}))
        graph = self.scan()
        self.assertIn('unsupported_review_decision', self.codes(graph))
        self.assertFalse(graph['acceptances'])

    def test_documented_hold_does_not_silently_replace_registry_selection(self):
        directory = self.plan()
        acceptance, digest = self.acceptance(directory)
        self.write(self.root / 'banks/e2_registry/one.json', dict(schema_version=1, stage='E2_active_registry',
            systems={WEAK: dict(acceptance=str(acceptance), sha256=digest)}))
        self.write(self.repo / 'examples/KG_Assoc/reviews/review/decision.json', dict(schema_version=1,
            stage='E2_scientific_review_decision', formal_acceptance=False,
            systems={WEAK: dict(status='acceptance_deferred_material_drift')}))
        graph = self.scan()
        self.assertEqual(catalog.system_record(graph, WEAK)['system']['selection'], 'selected_metadata_payload_deferred')
        self.assertIn('documented_hold_conflicts_with_registered_acceptance', self.codes(graph))


    def test_recovered_completion_retains_and_authenticates_historical_failure(self):
        directory = self.plan()
        failure = directory / 'r002/incomplete.json'
        failure_hash = self.write(failure, {'error': 'prepared code SHA changed'})
        auth = self.root / 'banks/e2_recoveries/recovery/authorization.json'
        auth_hash = self.write(auth, dict(schema_version=1, approved=True, purpose='e2_recovery',
            plan_sha256=hashlib.sha256((directory / 'plan.json').read_bytes()).hexdigest()))
        path = directory / 'r002/complete.json'
        completion = json.loads(path.read_text())
        completion.update(recovery_authorization=str(auth), output_sha256={str(failure): failure_hash, str(auth): auth_hash})
        self.write(path, completion)
        graph = self.scan()
        recovered = next(a for a in graph['attempts'] if a['replica'] == 2)
        self.assertEqual(recovered['execution'], 'completed_receipt')
        self.assertEqual(recovered['historical_failure']['data']['error'], 'prepared code SHA changed')
        self.write(auth, {'approved': False})
        graph = self.scan()
        recovered = next(a for a in graph['attempts'] if a['replica'] == 2)
        self.assertEqual(recovered['execution'], 'conflicting_evidence')


    def test_explicit_documented_supersession_recommends_without_accepting(self):
        sid = 'F04_N010_RP020_EE08_EA04'
        previous = self.repo / 'examples/KG_Assoc/reviews/z_old/decision.json'
        digest = self.write(previous, dict(schema_version=1, stage='E2_scientific_review_decision',
            formal_acceptance=False, systems={sid: dict(status='acceptance_deferred_material_drift', end_step=4000000)}))
        current = self.repo / 'examples/KG_Assoc/reviews/a_new/decision.json'
        record = dict(schema_version=1, stage='E2_scientific_review_decision', formal_acceptance=False,
            systems={sid: dict(status='qualified_acceptance_recommended_not_registered', end_step=6000000,
                supersedes_documented_review=dict(path=str(previous), sha256=digest))})
        self.write(current, record)
        graph = self.scan()
        system = catalog.system_record(graph, sid)['system']
        self.assertEqual(system['scientific'], 'qualified_acceptance_recommended_not_registered')
        self.assertEqual(system['selection'], 'missing')
        self.assertEqual(system['production_authorization'], 'absent')
        old = next(r for r in system['documented_reviews'] if r['status'] == 'acceptance_deferred_material_drift')
        self.assertTrue(old['superseded_by_documented_reviews'])
        self.assertFalse(graph['acceptances'])
        record['systems'][sid]['supersedes_documented_review']['sha256'] = 'changed'
        self.write(current, record)
        self.assertEqual(catalog.system_record(self.scan(), sid)['system']['scientific'], 'review_hold_material_drift')

    def test_recommendation_does_not_implicitly_supersede_old_hold(self):
        sid = 'F04_N010_RP020_EE08_EA04'
        for name, status in [('old', 'acceptance_deferred_material_drift'),
                             ('new', 'qualified_acceptance_recommended_not_registered')]:
            self.write(self.repo / f'examples/KG_Assoc/reviews/{name}/decision.json', dict(
                schema_version=1, stage='E2_scientific_review_decision', formal_acceptance=False,
                systems={sid: dict(status=status)}))
        self.assertEqual(catalog.system_record(self.scan(), sid)['system']['scientific'], 'review_hold_material_drift')

    def test_joint_summary_v2_is_metadata_supported_not_acceptance(self):
        path = self.root / 'aggregate/e2/review_summary/summary.json'
        self.write(path, dict(schema_version=2, stage='E2_joint_review_summary', automatic_acceptance=False))
        graph = self.scan()
        source = next(r for r in graph['records'] if r['path'] == str(path))
        self.assertTrue(source['supported'])
        self.assertFalse(graph['acceptances'])


if __name__ == '__main__':
    unittest.main()
