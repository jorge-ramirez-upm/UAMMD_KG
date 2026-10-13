"""Covariance-preserving peripheral population accounting; deterministic CPU fixtures."""
import copy
import unittest
import analyze_e2_peripheral_network as peripheral


class PeripheralTests(unittest.TestCase):
    def setUp(self):
        self.summary = dict(system=dict(number_of_stars=1000), windows_steps=1000000,
            records=[dict(replica=r, windows=[dict(start_step_exclusive=i*1000000,
                end_step_inclusive=(i+1)*1000000, segment='continuous', activity={},
                metrics={'components': dict(mean=10-i),
                         'largest_cluster_fraction': dict(mean=.980+i*.002)}) for i in range(6)])
                     for r in (1, 2, 3)])
        self.degrees = dict(records=[dict(replica=r, windows=[dict(start_step_exclusive=i*1000000,
            end_step_inclusive=(i+1)*1000000, segment='continuous',
            metrics={'degree_0_fraction': dict(mean=.005-i*.0005)}) for i in range(6)])
                                    for r in (1, 2, 3)])

    def test_subtracts_isolates_within_history_before_paired_statistics(self):
        original = copy.deepcopy(self.summary)
        result = peripheral.summarize(self.summary, self.degrees)
        self.assertEqual(self.summary, original)
        contrast = next(c for c in result['comparisons'] if c['observable']=='satellite_components'
                        and c['early_steps']==(2000000, 4000000) and c['late_steps']==(4000000, 6000000))
        self.assertEqual(contrast['per_replica_changes'], [-1, -1, -1])
        self.assertEqual(contrast['replicas'], 3)
        self.assertFalse(result['automatic_acceptance'])
        self.assertEqual(result['records'][0]['windows'][0]['start_step_exclusive'], 1000000)

    def test_misaligned_histograms_and_impossible_component_accounting_fail(self):
        data = copy.deepcopy(self.degrees)
        data['records'][0]['windows'][2]['start_step_exclusive'] += 1000
        with self.assertRaisesRegex(ValueError, 'window identities'):
            peripheral.summarize(self.summary, data)
        data = copy.deepcopy(self.summary)
        data['records'][0]['windows'][2]['metrics']['components']['mean'] = 1
        with self.assertRaisesRegex(ValueError, 'identities inconsistent'):
            peripheral.summarize(data, self.degrees)

    def test_published_f3_hold_dossier_binds_derived_sources_and_three_histories(self):
        import hashlib
        import json
        from pathlib import Path
        repo = Path(__file__).resolve().parents[3]
        base = repo/'examples/KG_Assoc/reviews/e2_f3_6m_20261013'
        decision = json.loads((base/'decision.json').read_text())
        self.assertFalse(decision['formal_acceptance'])
        for name, digest in decision['evidence_sha256'].items():
            self.assertEqual(hashlib.sha256((repo/name).read_bytes()).hexdigest(), digest)
        system = decision['systems']['F03_N010_RP080_EE08_EA04']
        self.assertEqual(system['status'], 'acceptance_deferred_material_drift')
        self.assertEqual([p['replica'] for p in system['reviewed_endpoints']], [1,2,3])
        self.assertTrue(all(p['end_step']==6000000 for p in system['reviewed_endpoints']))
        result = json.loads((base/'peripheral_population.json').read_text())
        self.assertFalse(result['automatic_acceptance'])
        c = next(c for c in result['comparisons'] if c['observable']=='satellite_components'
                 and c['early_steps']==[2000000,4000000] and c['late_steps']==[4000000,6000000])
        self.assertAlmostEqual(c['mean'], -.40766666666666684)
        self.assertEqual(c['replicas'], 3)
        summary=json.loads((base/'joint6m/summary.json').read_text())
        degrees=json.loads((base/'degree_distribution.json').read_text())
        for h,d in zip(summary['records'],degrees['records']):
            for w,g in zip(h['windows'],d['windows']):
                fractions=[g['metrics'][f'degree_{k}_fraction']['mean'] for k in range(4)]
                self.assertAlmostEqual(sum(fractions),1)
                self.assertAlmostEqual(sum(k*x for k,x in enumerate(fractions)),w['metrics']['mean_degree']['mean'])
                self.assertAlmostEqual(sum(k*k*x for k,x in enumerate(fractions)),w['metrics']['second_degree_moment']['mean'])


if __name__ == '__main__':
    unittest.main()
