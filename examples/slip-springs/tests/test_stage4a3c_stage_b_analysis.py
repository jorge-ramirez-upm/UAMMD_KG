import csv
import json
import tempfile
import unittest
from pathlib import Path

from stage4a3c_stage_b_analysis import analyze, terminal


class StageBAnalysisTest(unittest.TestCase):
    def test_terminal_pass_and_insufficient_support(self):
        rows = []
        for i in range(81):
            time = i * .1
            rows.append(dict(lag_time=time, H=__import__('math').exp(-time), H_se=1e-5,
                             pairs_per_chain=32, block_time=.01))
        self.assertEqual(terminal(rows)['status'], 'passed')
        self.assertEqual(terminal(rows[:12])['status'], 'insufficient_support')

    def test_reads_existing_six_channel_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'metadata.json').write_text(json.dumps(dict(steps=3, dt=.25, chains=2, springs=8, seed=433201)))
            (root / 'stress_metadata.json').write_text(json.dumps(dict(mode='every-step', frames=4, spacing=.25, levels=2, slots=2, coarsening=2)))
            fields = ('lag_samples', 'lag_time', 'block_samples', 'H', 'H_se', 'pairs_per_chain', 'pairs_total',
                      'Cxy', 'Cxz', 'Cyz', 'Cxx_yy', 'Cxx_zz', 'Cyy_zz')
            with (root / 'stress_correlations.csv').open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fields); writer.writeheader()
                for lag, pairs in ((0, 4), (1, 3)):
                    writer.writerow(dict(lag_samples=lag, lag_time=lag*.25, block_samples=1, H=.6, H_se=.01,
                                         pairs_per_chain=pairs, pairs_total=pairs*2, Cxy=1, Cxz=1, Cyz=1,
                                         Cxx_yy=0, Cxx_zz=0, Cyy_zz=0))
            result = analyze(root)
            self.assertEqual(result['independent_chain_clusters'], 2)
            self.assertEqual([row['pairs_per_chain'] for row in result['bins']], [4, 3])


if __name__ == '__main__':
    unittest.main()
