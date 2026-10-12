"""Deterministic joint-review bookkeeping fixtures; no GPU or convergence claims."""
import copy
from pathlib import Path
import tempfile
import unittest

from test_e2_g1 import fixture
import kg_assoc_e2 as e2
import analyze_joint_e2 as joint


class JointReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.sources = [dict(attempt=str(root / 'first'), plan=dict(smoke=False, system={}, parent_attempt=None), histories=[]),
                        dict(attempt=str(root / 'second'), plan=dict(smoke=False, system={}, parent_attempt=str(root / 'first')), histories=[])]
        for replica in (1, 2, 3):
            first = fixture(root / f'first_{replica}')
            second = fixture(root / f'second_{replica}', start=12000)
            old_rows, old_events, _ = e2.validation.validate(first)
            rows, events, _ = e2.validation.validate(second)
            # Fixture histories are bookkeeping replicas, not simulated independent samples.
            for entry in (first, second):
                entry['replica'] = replica
                entry['chemistry_seed'] = 420000 + replica
            second['md_seed'] += 100
            second['effective_md_seed'] = e2.validation.effective_md_seed(second['md_seed'])
            second['parent']['prefix'] = first['output_prefix']
            for field in ('creations', 'breaks'):
                offset = old_rows[-1][field] - rows[0][field]
                for row in rows:
                    row[field] += offset
            self.sources[0]['histories'].append(dict(entry=first, rows=old_rows, events=old_events))
            self.sources[1]['histories'].append(dict(entry=second, rows=rows, events=events))

    def test_restart_boundary_keeps_histories_and_windows_separate(self):
        summary = joint.summarize(self.sources, 6000)
        self.assertEqual(len(summary['records']), 3)
        windows = summary['records'][0]['windows']
        self.assertEqual([(w['start_step_exclusive'], w['end_step_inclusive']) for w in windows],
                         [(0, 6000), (6000, 12000), (12000, 18000), (18000, 24000)])
        self.assertFalse(summary['automatic_acceptance'])
        self.assertEqual(summary['scientific_status'], 'review_required')
        self.assertTrue(windows[0]['metrics']['L2']['constant_not_mixing_evidence'])
        self.assertTrue(windows[0]['metrics']['L2']['resolution_warning'])
        self.assertEqual(summary['late_segment_long_windows'][0]['window']['start_step_exclusive'], 12000)

    def test_seed_parent_step_boundary_and_replica_mismatches_fail(self):
        mutations = [('chemistry_seed', 1), ('md_seed', self.sources[0]['histories'][0]['entry']['md_seed']),
                     ('start_step', 11000)]
        for field, value in mutations:
            with self.subTest(field=field):
                sources = copy.deepcopy(self.sources)
                sources[1]['histories'][0]['entry'][field] = value
                with self.assertRaises(ValueError):
                    joint.check_lineage(sources)
        sources = copy.deepcopy(self.sources)
        sources[1]['histories'][0]['rows'][0]['L2'] += 1
        with self.assertRaisesRegex(ValueError, 'boundary state'):
            joint.check_lineage(sources)
        sources[1]['histories'].pop()
        with self.assertRaisesRegex(ValueError, 'three ordinary'):
            joint.check_lineage(sources)

    def test_pairing_uses_three_replica_changes_not_frames(self):
        records = [dict(windows=[dict(metrics={'L2': dict(mean=old)}),
                                 dict(metrics={'L2': dict(mean=new)})])
                   for old, new in ((10, 7), (20, 18), (30, 28))]
        result = joint.compare(records, 'metrics', 'L2', 0, 1)
        self.assertEqual(result['per_replica_changes'], [-3, -2, -2])
        self.assertEqual(result['replicas'], 3)
        self.assertLess(result['mean'], 0)
        self.assertTrue(result['excludes_zero'])

    def test_report_no_overwrite_and_no_automatic_acceptance(self):
        output = Path(self.temp.name) / 'report'
        summary = joint.summarize(self.sources, 6000)
        joint.write_report(summary, output)
        before = (output / 'REPORT.md').read_bytes()
        with self.assertRaises(FileExistsError):
            joint.write_report(summary, output)
        self.assertEqual((output / 'REPORT.md').read_bytes(), before)
        self.assertFalse(list(output.glob('*acceptance*')))


    def add_third_segment(self):
        third = copy.deepcopy(self.sources[1])
        third['attempt'] = 'third'
        third['plan']['parent_attempt'] = self.sources[1]['attempt']
        for index, h in enumerate(third['histories']):
            old = self.sources[1]['histories'][index]
            h['entry']['start_step'] += 12000
            h['entry']['end_step'] += 12000
            h['entry']['md_seed'] += 100
            h['entry']['effective_md_seed'] = e2.validation.effective_md_seed(h['entry']['md_seed'])
            h['entry']['parent']['prefix'] = old['entry']['output_prefix']
            h['entry']['output_prefix'] += '_third'
            for row in h['rows']:
                row['step'] += 12000
                row['time'] += 120
            for event in h['events']:
                event['step'] += 12000
            for field in ('creations', 'breaks'):
                offset = old['rows'][-1][field] - h['rows'][0][field]
                for row in h['rows']:
                    row[field] += offset
        self.sources.append(third)

    def test_six_windows_and_separate_long_windows_keep_three_units(self):
        self.add_third_segment()
        result = joint.summarize(self.sources, 6000)
        self.assertEqual(len(result['records']), 3)
        self.assertEqual(len(result['records'][0]['windows']), 6)
        self.assertEqual(len(result['segment_long_windows']), 2)
        self.assertTrue(all(c['replicas'] == 3 for c in result['comparisons']))
        self.assertTrue(all(c['early_window'] >= 1 for c in result['comparisons']))
        self.assertTrue(result['segment_comparisons'])
        output = Path(self.temp.name) / 'six_report'
        joint.write_report(result, output)
        text = (output / 'REPORT.md').read_text()
        self.assertIn('0.03–0.036M mean', text)
        self.assertFalse(result['automatic_acceptance'])

    def test_prior_estimates_reused_without_mutating_prior_evidence(self):
        prior = joint.summarize(self.sources, 6000)
        frozen = copy.deepcopy(prior)
        self.add_third_segment()
        result = joint.summarize(self.sources, 6000, dict(summary=prior, path='old-summary', sha256='bound'))
        self.assertEqual(prior, frozen)
        self.assertTrue(all('statistics_source' in w for w in result['records'][0]['windows'][:4]))
        self.assertTrue(all('statistics_source' not in w for w in result['records'][0]['windows'][4:]))
        self.assertEqual(result['records'][0]['windows'][3]['metrics'], prior['records'][0]['windows'][3]['metrics'])

    def test_wrong_4m_restart_seed_or_counter_is_rejected(self):
        self.add_third_segment()
        self.sources[2]['histories'][0]['entry']['md_seed'] = self.sources[1]['histories'][0]['entry']['md_seed']
        with self.assertRaisesRegex(ValueError, 'seed/parent'):
            joint.check_lineage(self.sources)

    def test_historical_review_driver_is_checked_against_committed_bytes(self):
        import hashlib
        from unittest.mock import patch
        source = '/repo/examples/KG_Assoc/analysis/analyze_joint_e2.py'
        payload = b'archived driver'
        with patch.object(joint.subprocess, 'check_output', return_value=payload):
            joint.authenticate_sources({source: hashlib.sha256(payload).hexdigest()}, 'original')
            with self.assertRaisesRegex(ValueError, 'recorded review driver'):
                joint.authenticate_sources({source: '0' * 64}, 'original')
        with patch.object(e2, 'check_hashes', side_effect=ValueError('physical source changed')):
            with self.assertRaisesRegex(ValueError, 'physical source changed'):
                joint.authenticate_sources({'physics.cuh': 'changed'}, 'original')


    def test_latest_executable_tampering_fails_after_historical_record_validation(self):
        from unittest.mock import patch
        root = Path(self.temp.name) / 'auth'
        plans = []
        attempts = []
        for index in (0, 1):
            attempt = root / f'attempt{index}'
            build_path = root / 'builds' / str(index) / 'manifest.json'
            build = dict(status='built', git_sha='commit', source_sha256={}, build_log_sha256={},
                         executable_sha256={'MD-binary': 'old' if index == 0 else 'latest'})
            e2.exclusive_json(build_path, build)
            plan = dict(smoke=False, git_sha='commit', source_sha256={}, build=build,
                executable_sha256=build['executable_sha256'], evidence_sha256={str(build_path): 'bound'},
                histories=[dict(replica=r, end_step=(index+1)*12000,
                    output_prefix=str(attempt / f'r{r:03d}/state')) for r in (1, 2, 3)])
            e2.exclusive_json(attempt / 'plan.json', plan)
            for entry in plan['histories']:
                e2.exclusive_json(Path(entry['output_prefix']).parent / 'complete.json',
                    dict(status='validated', plan_sha256=e2.campaign.sha256(attempt / 'plan.json'),
                         end_step=entry['end_step'], output_sha256={}))
            plans.append(plan)
            attempts.append(attempt)
        def hashes(values):
            if values.get('MD-binary') == 'old':
                raise AssertionError('historical bytes must not be claimed current')
            if values.get('MD-binary') == 'latest':
                raise ValueError('current executable changed')
        with patch.object(e2, 'check_plan', side_effect=plans), \
                patch.object(e2, 'approval_record'), \
                patch.object(e2, 'check_hashes', side_effect=hashes), \
                patch.object(e2.validation, 'validate', return_value=([], [], {})) as validate:
            with self.assertRaisesRegex(ValueError, 'current executable changed'):
                joint.authenticate(root, attempts)
            self.assertEqual(validate.call_count, 3)


    def test_published_6m_dossier_is_bound_and_remains_only_a_recommendation(self):
        import hashlib
        import json
        repo = Path(__file__).resolve().parents[3]
        dossier = repo / 'examples/KG_Assoc/reviews/e2_reassessment6m_20261013'
        decision = json.loads((dossier / 'decision.json').read_text())
        self.assertFalse(decision['formal_acceptance'])
        for name, digest in decision['evidence_sha256'].items():
            self.assertEqual(hashlib.sha256((repo / name).read_bytes()).hexdigest(), digest)
        system = decision['systems']['F04_N010_RP020_EE08_EA04']
        self.assertEqual(system['status'], 'qualified_acceptance_recommended_not_registered')
        reference = system['supersedes_documented_review']
        self.assertEqual(hashlib.sha256((repo / reference['path']).read_bytes()).hexdigest(),
                         reference['sha256'])
        self.assertEqual([e['replica'] for e in system['proposed_endpoints']], [1, 2, 3])
        self.assertTrue(all(e['end_step'] == 6000000 for e in system['proposed_endpoints']))
        self.assertTrue(all(len(e['state_sha256']) == 5 for e in system['proposed_endpoints']))
        config = json.loads((dossier / 'joint6m/analysis_config.json').read_text())
        self.assertEqual(hashlib.sha256(Path(joint.__file__).read_bytes()).hexdigest(),
                         config['analyzer_sha256'])
        provenance = json.loads((dossier / 'provenance.json').read_text())
        self.assertFalse(provenance['production_authorization'])
        self.assertEqual(len(provenance['segments']), 3)
        self.assertTrue(all(len(s['histories']) == 3 for s in provenance['segments']))



if __name__ == '__main__':
    unittest.main()
